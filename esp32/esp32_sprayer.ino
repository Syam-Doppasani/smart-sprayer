#include <WiFi.h>
#include <WiFiUdp.h>
#include <WebServer.h>

// ===================== USER CONFIG =====================
// Wi‑Fi credentials
static const char* WIFI_SSID = "-----";
static const char* WIFI_PASS = "-----";

// PC receiver (run a UDP listener on this IP/port)
// Tip: set this to your laptop/PC LAN IP (e.g. 192.168.1.10)
static const char* PC_UDP_IP = "192.168.80.1";
static const uint16_t PC_UDP_PORT = 5005;

// ESP32 HTTP server port
static const uint16_t HTTP_PORT = 80;

// Sprayer output pin (change to your relay/MOSFET pin)
static const int SPRAY_PIN = 23;
static const bool SPRAY_ACTIVE_HIGH = true; // set false if your relay is active-low

// Telemetry rate (keep modest to avoid Wi‑Fi congestion)
static const uint32_t TELEMETRY_INTERVAL_MS = 100; // 10 Hz

// Buffer for smooth flow during Wi‑Fi hiccups
static const size_t TX_QUEUE_SIZE = 64;
// =======================================================

static WiFiUDP udp;
static WebServer server(HTTP_PORT);

static volatile bool spraying = false;
static uint32_t spray_until_ms = 0;

struct TxItem {
  uint32_t seq;
  uint32_t ms;
  bool spraying;
  int rssi;
};

static TxItem txq[TX_QUEUE_SIZE];
static size_t txq_head = 0; // next write
static size_t txq_tail = 0; // next read
static uint32_t seqno = 0;

static uint32_t last_wifi_check = 0;
static uint32_t last_telemetry = 0;

static inline void setSpray(bool on) {
  spraying = on;
  const bool level = SPRAY_ACTIVE_HIGH ? on : !on;
  digitalWrite(SPRAY_PIN, level ? HIGH : LOW);
}

static bool txq_is_full() {
  return ((txq_head + 1) % TX_QUEUE_SIZE) == txq_tail;
}
static bool txq_is_empty() {
  return txq_head == txq_tail;
}

static void txq_push(const TxItem& item) {
  if (txq_is_full()) {
    // Drop oldest to keep stream moving (smooth realtime > perfect history)
    txq_tail = (txq_tail + 1) % TX_QUEUE_SIZE;
  }
  txq[txq_head] = item;
  txq_head = (txq_head + 1) % TX_QUEUE_SIZE;
}

static bool txq_pop(TxItem& out) {
  if (txq_is_empty()) return false;
  out = txq[txq_tail];
  txq_tail = (txq_tail + 1) % TX_QUEUE_SIZE;
  return true;
}

static void wifi_ensure_connected() {
  if (WiFi.status() == WL_CONNECTED) return;

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false); // reduce latency/jitter
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  // Non-blocking connect attempt (brief)
  const uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - start) < 2000) {
    delay(50);
    yield();
  }
}

static void send_udp_item(const TxItem& item) {
  // Tiny JSON (no dynamic allocation)
  char buf[128];
  const int n = snprintf(
    buf, sizeof(buf),
    "{\"seq\":%lu,\"ms\":%lu,\"spraying\":%d,\"rssi\":%d}",
    (unsigned long)item.seq,
    (unsigned long)item.ms,
    item.spraying ? 1 : 0,
    item.rssi
  );
  if (n <= 0) return;

  udp.beginPacket(PC_UDP_IP, PC_UDP_PORT);
  udp.write((const uint8_t*)buf, (size_t)n);
  udp.endPacket();
}

static void flush_udp_queue() {
  if (WiFi.status() != WL_CONNECTED) return;
  // Flush a few items per loop to keep latency low
  for (int i = 0; i < 6; i++) {
    TxItem item;
    if (!txq_pop(item)) return;
    send_udp_item(item);
  }
}

static void enqueue_telemetry() {
  TxItem item;
  item.seq = ++seqno;
  item.ms = millis();
  item.spraying = spraying;
  item.rssi = (WiFi.status() == WL_CONNECTED) ? WiFi.RSSI() : -127;
  txq_push(item);
}

// ===================== HTTP handlers =====================
static void handle_status() {
  char buf[256];
  IPAddress ip = WiFi.localIP();
  const int n = snprintf(
    buf, sizeof(buf),
    "{\"ip\":\"%u.%u.%u.%u\",\"wifi\":%d,\"rssi\":%d,\"spraying\":%d,\"uptime_ms\":%lu}",
    ip[0], ip[1], ip[2], ip[3],
    (WiFi.status() == WL_CONNECTED) ? 1 : 0,
    (WiFi.status() == WL_CONNECTED) ? WiFi.RSSI() : -127,
    spraying ? 1 : 0,
    (unsigned long)millis()
  );
  server.send(200, "application/json", String(buf, (size_t)n));
}

static void handle_spray() {
  uint32_t ms = 250;
  if (server.hasArg("ms")) {
    ms = (uint32_t)server.arg("ms").toInt();
    if (ms < 10) ms = 10;
    if (ms > 5000) ms = 5000;
  }
  setSpray(true);
  spray_until_ms = millis() + ms;
  server.send(200, "text/plain", "OK");
}

static void handle_stop() {
  spray_until_ms = 0;
  setSpray(false);
  server.send(200, "text/plain", "OK");
}

static void handle_not_found() {
  server.send(404, "text/plain", "Not Found");
}
// =========================================================

void setup() {
  Serial.begin(115200);

  pinMode(SPRAY_PIN, OUTPUT);
  setSpray(false);

  wifi_ensure_connected();

  udp.begin(PC_UDP_PORT); // binds local port (not strictly required, but fine)

  server.on("/status", HTTP_GET, handle_status);
  server.on("/spray", HTTP_POST, handle_spray);
  server.on("/stop", HTTP_POST, handle_stop);
  server.onNotFound(handle_not_found);
  server.begin();
}

void loop() {
  server.handleClient();

  const uint32_t now = millis();

  // Safety: auto-stop after requested duration
  if (spraying && spray_until_ms != 0 && (int32_t)(now - spray_until_ms) >= 0) {
    spray_until_ms = 0;
    setSpray(false);
  }

  // Periodic Wi‑Fi keepalive
  if ((now - last_wifi_check) >= 1000) {
    last_wifi_check = now;
    wifi_ensure_connected();
  }

  // Telemetry tick
  if ((now - last_telemetry) >= TELEMETRY_INTERVAL_MS) {
    last_telemetry = now;
    enqueue_telemetry();
  }

  // Smooth send (burst small batches)
  flush_udp_queue();

  delay(2);
}
