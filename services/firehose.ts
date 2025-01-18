import WebSocket from 'ws';

interface RepoOperation {
  action: string;
  path: string;
}

interface RepoEvent {
  repo: string;
  ops: RepoOperation[];
}

class RepoStreamCallbacks {
  repoCommit(evt: RepoEvent): void {
    console.log("Event from", evt.repo);
    for (const op of evt.ops) {
      console.log(` - ${op.action} record ${op.path}`);
    }
  }
}

class SequentialScheduler {
  private name: string;
  private eventHandler: (evt: RepoEvent) => void;

  constructor(name: string, eventHandler: (evt: RepoEvent) => void) {
    this.name = name;
    this.eventHandler = eventHandler;
  }

  async handleEvent(evt: RepoEvent): Promise<void> {
    try {
      this.eventHandler(evt);
    } catch (error) {
      console.error(`Error handling event in scheduler "${this.name}":`, error);
    }
  }
}

const connectToFirehose = (uri: string, callbacks: RepoStreamCallbacks): void => {
  const websocket = new WebSocket(uri);
  const scheduler = new SequentialScheduler("myfirehose", callbacks.repoCommit.bind(callbacks));

  websocket.on('open', () => {
    console.log("WebSocket connection established.");
    websocket.on('message', async (data: WebSocket.RawData) => {
      try {
        const decodedData: RepoEvent = JSON.parse(data.toString()); // Replace with CBOR decoding if needed
        await scheduler.handleEvent(decodedData);
      } catch (error) {
        console.error("Error processing message:", error);
      }
    });
  });

  websocket.on('error', (error: Error) => {
    console.error("WebSocket error:", error);
  });

  websocket.on('close', () => {
    console.log("WebSocket connection closed.");
  });
};

export { connectToFirehose, RepoStreamCallbacks };
