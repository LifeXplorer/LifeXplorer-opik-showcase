# langchainjs-fastify-boardgame-chat

*A board-game cafe chat widget whose conversations read like conversations in Opik.*

## The problem

Each message a guest types is one `POST /chat`, so a three-question chat is three unrelated traces. Opik's Threads tab can stitch them back together, but only if the root run's input and output are plain text; wrap them in objects and the transcript fills up with JSON.

## What you'll build

A Fastify server for the Meeple & Brew cafe widget. A LangChain.js chain takes the guest's message as a string, shortlists games from a fictional catalog in `data/games.json`, and returns the host's reply as a string. A second chain, `/chat-envelope`, does the same work with object-in, object-out, so you can compare the two threads side by side.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY`.
2. `npm install`
3. `npm run demo`
4. `npm test`

*Built with Opik. Inspired by Opik's examples and documentation.*
