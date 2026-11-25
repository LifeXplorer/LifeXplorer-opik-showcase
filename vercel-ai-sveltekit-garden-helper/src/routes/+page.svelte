<script lang="ts">
  import { Chat } from "@ai-sdk/svelte";

  const chat = new Chat({});
  let input = $state("");
  const busy = $derived(chat.status === "submitted" || chat.status === "streaming");

  function send(event: SubmitEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    chat.sendMessage({ text });
    input = "";
  }
</script>

<main>
  <h1>Sprout, the Hollyhock Lane garden helper</h1>
  <p class="hint">Ask about sowing dates, watering, pests or bed planning.</p>

  <div class="log">
    {#each chat.messages as message (message.id)}
      <div class="row {message.role}">
        <div class="bubble">
          {#each message.parts as part}
            {#if part.type === "text"}<span>{part.text}</span>{/if}
          {/each}
        </div>
      </div>
    {/each}
  </div>

  <form onsubmit={send}>
    <input bind:value={input} placeholder="When should I plant out tomatoes?" disabled={busy} />
    <button disabled={busy || !input.trim()}>Send</button>
  </form>
</main>

<style>
  :global(body) { margin: 0; font-family: system-ui, sans-serif; background: #f4f7f1; color: #1d2a1b; }
  main { max-width: 640px; margin: 0 auto; padding: 2rem 1rem; min-height: 100vh; box-sizing: border-box; display: flex; flex-direction: column; }
  h1 { font-size: 1.25rem; margin: 0 0 0.25rem; }
  .hint { margin: 0 0 1rem; color: #5b6b57; font-size: 0.9rem; }
  .log { flex: 1; }
  .row { display: flex; margin: 0.6rem 0; }
  .row.user { justify-content: flex-end; }
  .bubble { max-width: 85%; padding: 0.6rem 0.9rem; border-radius: 12px; line-height: 1.45; white-space: pre-wrap; background: #fff; border: 1px solid #d9e2d4; }
  .user .bubble { background: #2f7d32; color: #fff; border: none; }
  form { display: flex; gap: 0.5rem; margin-top: 1rem; }
  input { flex: 1; padding: 0.6rem 0.8rem; border: 1px solid #c4d1bf; border-radius: 8px; font: inherit; }
  button { padding: 0.6rem 1.1rem; border: none; border-radius: 8px; background: #2f7d32; color: #fff; font: inherit; cursor: pointer; }
  button:disabled { opacity: 0.5; cursor: default; }
</style>
