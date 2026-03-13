/**
 * WebSocket MQTT client for frontend
 */

interface MQTTMessage {
  topic: string;
  payload: any;
}

class WebSocketMQTTClient {
  private ws: WebSocket | null = null;
  private listeners: Map<string, (data: any) => void> = new Map();

  connect() {
    this.ws = new WebSocket('ws://localhost:9001');

    this.ws.onopen = () => {
      console.log('✓ Connected to MQTT via WebSocket');
    };

    this.ws.onclose = () => {
      console.log('✗ Disconnected from MQTT WebSocket');
    };

    this.ws.onmessage = (event) => {
      try {
        const message: MQTTMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
  }

  private handleMessage(message: MQTTMessage) {
    const { topic, payload } = message;
    
    // Route messages to appropriate listeners
    if (topic.includes('/telemetry')) {
      this.notifyListeners('telemetry', payload);
    } else if (topic.includes('/heartbeat')) {
      this.notifyListeners('heartbeat', payload);
    }
  }

  private notifyListeners(type: string, data: any) {
    const listener = this.listeners.get(type);
    if (listener) {
      listener(data);
    }
  }

  subscribe(type: 'telemetry' | 'heartbeat', callback: (data: any) => void) {
    this.listeners.set(type, callback);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const mqttClient = new WebSocketMQTTClient();