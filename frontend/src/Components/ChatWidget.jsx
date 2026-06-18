import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { MdClose, MdSend, MdChat, MdKeyboardArrowDown } from "react-icons/md";
import { HiSparkles } from "react-icons/hi2";
import { streamChatMessage } from "../redux/features/chatbot/chatbotApiSlice";
import { useGetProductDetailsQuery } from "../redux/features/product/productApiSlice";

// ── Small product reference card rendered inside assistant messages ────────────

const ProductCard = ({ productId }) => {
  const navigate = useNavigate();
  const { data: product, isLoading } = useGetProductDetailsQuery(productId, {
    skip: !productId,
  });

  if (isLoading || !product) return null;

  return (
    <div
      onClick={() => navigate(`/sales/${product.product_id}`)}
      className="flex items-center gap-2 mt-2 border border-zinc-700 hover:border-white p-2 cursor-pointer transition-colors group"
    >
      {product.images?.[0]?.image_url && (
        <img
          src={product.images[0].image_url}
          alt={product.title}
          className="w-10 h-10 object-cover flex-shrink-0"
        />
      )}
      <div className="min-w-0">
        <p className="text-white text-xs font-medium truncate">
          {product.title}
        </p>
        <p className="text-zinc-400 text-xs">£{product.price}</p>
      </div>
    </div>
  );
};

// ── Individual message bubble ─────────────────────────────────────────────────

const MessageBubble = ({ message }) => {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[85%] ${
          isUser
            ? "bg-zinc-800 text-white"
            : "bg-transparent border border-zinc-700 text-zinc-100"
        } px-3 py-2 text-sm leading-relaxed`}
      >
        {/* Stream cursor shown while streaming */}
        <span className="whitespace-pre-wrap">
          {message.content}
          {message.streaming && (
            <span className="inline-block w-1 h-3 bg-white ml-0.5 animate-pulse" />
          )}
        </span>

        {/* Product cards for referenced products */}
        {!message.streaming &&
          message.productIds?.map((pid) => (
            <ProductCard key={pid} productId={pid} />
          ))}
      </div>
    </div>
  );
};

// ── Suggested prompts shown on empty state ────────────────────────────────────

const SUGGESTED_PROMPTS = [
  "Show me your latest products",
  "What styles do you have available?",
  "Do you have anything in red?",
  "What's currently in stock?",
];

// ── Main ChatWidget component ─────────────────────────────────────────────────

const ChatWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const abortControllerRef = useRef(null);

  const { isAuthenticated } = useSelector((state) => state.auth);

  // Retrieve or create anonymous session key
  const sessionKey = useRef(
    localStorage.getItem("session_key") ||
      (() => {
        const key = crypto.randomUUID();
        localStorage.setItem("session_key", key);
        return key;
      })(),
  );

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Clean up any in-flight stream on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const sendMessage = useCallback(
    async (text) => {
      const trimmed = text.trim();
      if (!trimmed || isSending) return;

      setInput("");
      setIsSending(true);

      // Add user message
      const userMsg = {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
      };
      setMessages((prev) => [...prev, userMsg]);

      // Add placeholder assistant message for streaming
      const assistantId = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          streaming: true,
          productIds: [],
        },
      ]);

      abortControllerRef.current = streamChatMessage({
        message: trimmed,
        sessionId,
        sessionKey: isAuthenticated ? null : sessionKey.current,
        onToken: (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + token } : m,
            ),
          );
        },
        onDone: ({ messageId, productIds }) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, streaming: false, productIds } : m,
            ),
          );
          // Persist session ID for multi-turn continuity
          if (!sessionId && messageId) {
            // Backend returns message_id not session_id here —
            // we store it in a follow-up fetch if needed; for now
            // sessionId stays null and Django matches on session_key
          }
          setIsSending(false);
        },
        onError: () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content:
                      "Sorry, I couldn't connect right now. Please try again.",
                    streaming: false,
                  }
                : m,
            ),
          );
          setIsSending(false);
        },
      });
    },
    [isSending, sessionId, isAuthenticated],
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  return (
    <>
      {/* Floating toggle button */}
      <button
        onClick={() => setIsOpen((o) => !o)}
        className="fixed bottom-6 right-6 z-40 w-14 h-14 bg-white text-black flex items-center justify-center shadow-2xl hover:bg-zinc-200 transition-colors"
        aria-label="Toggle chat"
      >
        {isOpen ? (
          <MdKeyboardArrowDown className="w-6 h-6" />
        ) : (
          <MdChat className="w-6 h-6" />
        )}
      </button>

      {/* Chat panel */}
      {isOpen && (
        <div
          className="fixed bottom-24 right-6 z-40 w-80 sm:w-96 bg-black border border-zinc-700 shadow-2xl flex flex-col"
          style={{ height: "520px" }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 flex-shrink-0">
            <div className="flex items-center gap-2">
              <HiSparkles className="w-4 h-4 text-white" />
              <span className="text-white text-sm font-medium">
                SweetLatex Assistant
              </span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-zinc-500 hover:text-white transition-colors"
            >
              <MdClose className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-1">
            {messages.length === 0 ? (
              /* Empty state with suggested prompts */
              <div className="h-full flex flex-col justify-center">
                <p className="text-zinc-500 text-xs text-center mb-4">
                  Ask me anything about our products
                </p>
                <div className="space-y-2">
                  {SUGGESTED_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => sendMessage(prompt)}
                      className="w-full text-left text-xs text-zinc-400 border border-zinc-800 hover:border-zinc-600 hover:text-white px-3 py-2 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form
            onSubmit={handleSubmit}
            className="flex items-center gap-2 px-3 py-3 border-t border-zinc-800 flex-shrink-0"
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about products..."
              disabled={isSending}
              className="flex-1 bg-zinc-900 text-white text-sm placeholder-zinc-600 border border-zinc-700 focus:border-zinc-500 outline-none px-3 py-2 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!input.trim() || isSending}
              className="p-2 border border-zinc-700 text-white hover:border-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex-shrink-0"
              aria-label="Send message"
            >
              <MdSend className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
    </>
  );
};

export default ChatWidget;
