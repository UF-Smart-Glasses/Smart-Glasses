#include "udp.h"
#include "config.h"
#include <WiFi.h>
#include "lwip/sockets.h"

static int sock = -1;
static struct sockaddr_in dest_addr;
static uint32_t tx_sequence = 0; //counter for sequence number
constexpr size_t UDP_HEADER_SIZE = 5;

// Helper for sending packets (audio and video)
static bool send_packet(uint8_t type, const uint8_t *payload, size_t payload_size){
    size_t packet_size = 1 + sizeof(uint32_t) + payload_size; // calculate packet size

    uint8_t *send_buf = (uint8_t *)malloc(packet_size); // allocate memory matching packet size

    if (!send_buf) {
        return false;   // if it doesnt work
    }
    // Build Packet:
    // type:
    send_buf[0] = type;                     // first byte: frame type (video or audio)
    // sequence:
    uint32_t sequence = htonl(tx_sequence); // convert number to network order
    memcpy(&send_buf[1], &sequence, sizeof(sequence)); // copy 4‑byte seq
    // payload:
    memcpy(&send_buf[1 + sizeof(sequence)], payload, payload_size); // place payload right after sequence

    // send:
    int result = sendto(sock, send_buf, packet_size, 0, (struct sockaddr *)&dest_addr, sizeof(dest_addr));

    free(send_buf);           // free memory

    if (result < 0) {
        return false;         // transmission failed
    }
    tx_sequence++;            // advance counter for the next packet
    return true;              // success
}

void setupNetwork(const char* ssid, const char* password, const char* server_ip, const int port) {
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConnected to WiFi");

    dest_addr.sin_addr.s_addr = inet_addr(server_ip);
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(port);

    sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    if (sock < 0) {
        Serial.println("Unable to create UDP socket");
    }
}

void udp_send_task(void *pvParameters) {
    video_frame_t video_frame;
    audio_buffer_t audio_buf;

    while(1) {
        if (sock < 0) {
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }

        // udp: fire and forget
        
        while (xQueueReceive(audio_tx_queue, &audio_buf, 0) == pdTRUE) {
            send_packet(WS_FRAME_AUDIO_TX, reinterpret_cast<uint8_t *>(audio_buf.samples), audio_size);
        }

        while (xQueueReceive(video_queue, &video_frame, 0) == pdTRUE) {
            send_packet(WS_FRAME_VIDEO, video_frame.data, video_frame.len);
        }

        vTaskDelay(pdMS_TO_TICKS(5)); // wait 5 ms
    }
}