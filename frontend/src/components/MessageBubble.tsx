import { useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
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

/**
 * 소크라테스식 후속 질문을 본문에서 분리한다.
 * 마지막 줄이 "?"로 끝나면 후속 질문으로 간주.
 */
function extractSocraticQuestion(content: string): { body: string; question: string | null } {
  const lines = content.trimEnd().split("\n");
  if (lines.length < 2) return { body: content, question: null };

  const lastLine = (lines[lines.length - 1] ?? "").trim();
  if (lastLine.endsWith("?")) {
    return {
      body: lines.slice(0, -1).join("\n").trimEnd(),
      question: lastLine,
    };
  }
  return { body: content, question: null };
}

function CodeBlock({ language, children }: { language: string; children: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(children).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [children]);

  return (
    <div className="code-block-wrapper">
      <div className="code-block-header">
        <span className="code-block-lang">{language || "code"}</span>
        <button className="code-copy-btn" onClick={handleCopy}>
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <SyntaxHighlighter
        style={oneLight}
        language={language || "text"}
        PreTag="div"
        customStyle={{ margin: 0, borderRadius: "0 0 8px 8px", fontSize: "13px" }}
      >
        {children}
      </SyntaxHighlighter>
    </div>
  );
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isAi = !isUser;

  const { body, question } = isAi && !message.isStreaming
    ? extractSocraticQuestion(message.content)
    : { body: message.content, question: null };

  return (
    <div className={`message-row ${isUser ? "message-row--user" : "message-row--ai"}`}>
      {isAi && <div className="message-avatar">AI</div>}
      <div className="message-body">
        <div className={`message-bubble ${isUser ? "bubble--user" : "bubble--ai"}`}>
          {isUser ? (
            <p className="message-text">
              {message.content}
            </p>
          ) : (
            <div className="ai-message-content">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || "");
                    const codeStr = String(children).replace(/\n$/, "");
                    if (match) {
                      return <CodeBlock language={match[1] ?? "text"}>{codeStr}</CodeBlock>;
                    }
                    return <code className="inline-code" {...props}>{children}</code>;
                  },
                  p({ children }) {
                    return <p className="md-p">{children}</p>;
                  },
                  ul({ children }) {
                    return <ul className="md-ul">{children}</ul>;
                  },
                  ol({ children }) {
                    return <ol className="md-ol">{children}</ol>;
                  },
                  li({ children }) {
                    return <li className="md-li">{children}</li>;
                  },
                  blockquote({ children }) {
                    return <blockquote className="md-blockquote">{children}</blockquote>;
                  },
                }}
              >
                {body}
              </ReactMarkdown>
              {message.isStreaming && <span className="streaming-cursor" />}
            </div>
          )}
        </div>
        {question && (
          <div className="socratic-question">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{question}</ReactMarkdown>
          </div>
        )}
        <span className="message-time">{formatTime(message.timestamp)}</span>
      </div>
    </div>
  );
}
