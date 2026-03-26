import "@/styles/ChatRoom.css";

export interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface MessageBubbleProps {
  message: Message;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "message-row--user" : "message-row--ai"}`}>
      {!isUser && <div className="message-avatar">AI</div>}
      <div className="message-body">
        <div className={`message-bubble ${isUser ? "bubble--user" : "bubble--ai"}`}>
          <p className="message-text">
            {message.content}
            {message.isStreaming && <span className="streaming-cursor" />}
          </p>
        </div>
        <span className="message-time">{formatTime(message.timestamp)}</span>
      </div>
    </div>
  );
}
