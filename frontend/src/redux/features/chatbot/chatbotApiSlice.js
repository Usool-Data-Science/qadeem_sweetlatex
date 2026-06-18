import { apiSlice } from "../../services/apiSlice";

export const chatbotApiSlice = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // GET /api/chatbot/sessions/
    getChatSessions: builder.query({
      query: () => "/chatbot/sessions/",
      providesTags: ["ChatSessions"],
    }),

    // GET /api/chatbot/sessions/<id>/
    getChatSession: builder.query({
      query: (sessionId) => `/chatbot/sessions/${sessionId}/`,
      providesTags: (result, error, id) => [{ type: "ChatSessions", id }],
    }),

    // DELETE /api/chatbot/sessions/<id>/
    deleteChatSession: builder.mutation({
      query: (sessionId) => ({
        url: `/chatbot/sessions/${sessionId}/`,
        method: "DELETE",
      }),
      invalidatesTags: ["ChatSessions"],
    }),
  }),
});

export const {
  useGetChatSessionsQuery,
  useGetChatSessionQuery,
  useDeleteChatSessionMutation,
} = chatbotApiSlice;

// ── SSE streaming helper (not RTK Query — SSE requires native EventSource) ──
// Returns a controller object with a .abort() method.
// onToken(token) is called for each streamed token.
// onDone({ messageId, productIds }) is called when the stream completes.
// onError(err) is called on failure.

const BASE_API_URL = import.meta.env.VITE_API_BASE_URL || "";

export function streamChatMessage({
  message,
  sessionId,
  sessionKey,
  onToken,
  onDone,
  onError,
}) {
  const controller = new AbortController();

  fetch(`${BASE_API_URL}/api/chatbot/chat/`, {
    method: "POST",
    credentials: "include",
    signal: controller.signal,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId || null,
      session_key: sessionKey || null,
    }),
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`Chat request failed: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep incomplete line in buffer

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const payload = JSON.parse(line.slice(6));
            if (payload.token !== undefined) {
              onToken(payload.token);
            } else if (payload.done) {
              onDone({
                messageId: payload.message_id,
                productIds: payload.product_ids || [],
              });
            }
          } catch {
            // Malformed SSE line — skip
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        onError(err);
      }
    });

  return controller;
}
