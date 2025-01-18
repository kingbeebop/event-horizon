"use client";

import { useEffect, useState } from "react";
import { 
  Box,
  Container,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  CircularProgress,
  ThemeProvider,
  createTheme,
  CssBaseline,
} from "@mui/material";
import * as cbor from 'cborg';

interface RepoOperation {
  action: string;
  path: string;
}

interface RepoEvent {
  repo: string;
  ops: RepoOperation[];
  time?: string;
}

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    }
  }
});

export default function Home() {
  const [mounted, setMounted] = useState(false);
  const [events, setEvents] = useState<RepoEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!mounted) return;
    
    const uri = "wss://bsky.network/xrpc/com.atproto.sync.subscribeRepos";
    const websocket = new WebSocket(uri, ['cbor']);

    websocket.binaryType = 'arraybuffer';

    websocket.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    websocket.onmessage = (event) => {
      try {
        const buffer = event.data;
        const data = cbor.decode(new Uint8Array(buffer).slice(1));
        
        if (data.ops) {
          const newEvent: RepoEvent = {
            repo: data.repo,
            ops: data.ops,
            time: new Date().toISOString()
          };
          
          setEvents(prev => [newEvent, ...prev].slice(0, 100));
        }
      } catch (err) {
        console.error("Error processing message:", err);
      }
    };

    websocket.onerror = (err) => {
      console.error("WebSocket error:", err);
      setError("WebSocket connection error");
      setIsConnected(false);
    };

    websocket.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      websocket.close();
    };
  }, [mounted]);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Bluesky Firehose
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Alert 
            severity={isConnected ? "success" : "warning"}
            sx={{ mb: 2 }}
          >
            {isConnected ? "Connected to firehose" : "Disconnected"}
          </Alert>
        </Box>

        {!events.length && isConnected && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}

        <List>
          {events.map((event, index) => (
            <Paper 
              key={`${event.time}-${index}`}
              elevation={2} 
              sx={{ mb: 2, p: 2 }}
            >
              <Typography variant="subtitle2" color="text.secondary">
                {event.time}
              </Typography>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>
                Repository: {event.repo}
              </Typography>
              <Typography variant="h6" sx={{ mb: 1 }}>
                Operations:
              </Typography>
              <List dense>
                {event.ops.map((op, opIndex) => (
                  <ListItem key={opIndex}>
                    <ListItemText
                      primary={`${op.action} - ${op.path}`}
                    />
                  </ListItem>
                ))}
              </List>
              {index < events.length - 1 && <Divider sx={{ mt: 2 }} />}
            </Paper>
          ))}
        </List>
      </Container>
    </ThemeProvider>
  );
}
