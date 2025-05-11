"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { BACKEND_PUBLIC_WS_URL } from "@/lib/api-utils";

type Message = {
  id: string;
  content: string;
  sender_type: "user" | "assistant";
  createdAt: Date;
  isComplete: boolean;
};


type ChunkType = "start" | "chunk" | "end";

type MessageChunk = {
  message_id: string;
  type: ChunkType;
  content?: string;
};


export default function Chat() {
  const [currentWs, setCurrentWs] = useState<WebSocket>();
  const [connectionStatus, setConnectionStatus] = useState<
    "connected" | "disconnected" | "error"
  >("disconnected");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>(null);

  const connectWebSocket = useCallback(() => {
    const ws = new WebSocket(`${BACKEND_PUBLIC_WS_URL}/ws/chat`);

    ws.onopen = () => {
      setConnectionStatus("connected");

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      const messageChunk = JSON.parse(event.data) as MessageChunk;

      console.log(messageChunk);

      if (messageChunk.type === "start") {
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            id: messageChunk.message_id,
            content: "",
            sender_type: "assistant",
            createdAt: new Date(),
            isComplete: false,
          },
        ]);
      } else if (messageChunk.type === "chunk") {
        setMessages((prevMessages) => {
          return prevMessages.map((message) => {
            if (message.id === messageChunk.message_id) {
              message.content += messageChunk.content;
            }
            return message;
          });
        });
      } else if (messageChunk.type === "end") {
        setMessages((prevMessages) => {
          return prevMessages.map((message) => {
            if (message.id === messageChunk.message_id) {
              message.isComplete = true;
            }
            return message;
          });
        });
      }
    };

    ws.onerror = () => {
      setConnectionStatus("error");
    };

    ws.onclose = (event) => {
      setConnectionStatus("disconnected");

      if (event.code === 1000) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 1000);
      }
    };

    setCurrentWs(ws);

    return ws;
  }, []);

  const sendMessage = () => {
    if (!currentWs || !input) {
      return;
    }
    setMessages((prevMessages) => [
      ...prevMessages,
      {
        id: crypto.randomUUID(),
        content: input,
        sender_type: "user",
        createdAt: new Date(),
        isComplete: false,
      },
    ]);
    setInput("");

    if (currentWs.readyState === WebSocket.OPEN) {
      currentWs.send(input);
    } else {
      setConnectionStatus("error");

      if (currentWs.readyState === WebSocket.CLOSED) {
        connectWebSocket();
      }
    }
  };

  useEffect(() => {
    const ws = connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      ws.close();
    };
  }, [connectWebSocket]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full p-4">
      <h1 className="text-2xl font-bold mb-4">Chat</h1>
      <div className="text-sm mb-2">
        Connection status:{" "}
        <span
          className={`font-semibold ${connectionStatus === "connected"
            ? "text-green-500"
            : connectionStatus === "error"
              ? "text-red-500"
              : "text-yellow-500"
            }`}
        >
          {connectionStatus}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto mb-4 border rounded-md p-4">
        {messages.length === 0 ? (
          <p className="text-center text-muted-foreground">
            No messages yet. Start a conversation!
          </p>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`mb-4 ${message.sender_type === "user" ? "text-right" : "text-left"}`}
            >
              <div
                className={`inline-block px-4 py-2 rounded-lg ${message.sender_type === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
                  }`}
              >
                {message.content}
                {!message.isComplete && message.sender_type === "assistant" && (
                  <span className="ml-1 animate-pulse">▌</span>
                )}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {message.createdAt.toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type your message..."
          className="flex-1"
        />
        <Button
          onClick={sendMessage}
          disabled={connectionStatus !== "connected"}
        >
          Send
        </Button>
      </div>
    </div>
  );
}
