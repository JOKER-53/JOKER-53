// gen-snake.mjs
// Uses the documented JS API of generate-snake-animation (avoids guessing
// undocumented CLI flags). Run with: node gen-snake.mjs
//
// Requires: npm install generate-snake-animation (or npx will fetch it)

import { generateSnakeAnimation } from "generate-snake-animation";
import fs from "fs";

const GH_USER = process.env.GH_USER || "JOKER-53";
const GH_TOKEN = process.env.GH_TOKEN;

if (!GH_TOKEN) {
  console.error("ERROR: set GH_TOKEN env var first");
  process.exit(1);
}

const outputs = [
  { format: "svg", drawOptions: {} }, // default palette -> github-snake.svg
  {
    format: "svg",
    drawOptions: {
      colorDots: ["#1A1F26", "#103B44", "#1A6E70", "#4FD1C5", "#FFDE59"],
      colorSnake: "#FF5A36",
    },
  }, // brutalist palette -> github-snake-brutalist.svg
];

const results = await generateSnakeAnimation(
  {
    platform: "github",
    username: GH_USER,
    githubToken: GH_TOKEN,
  },
  outputs,
);

fs.mkdirSync("dist", { recursive: true });
fs.writeFileSync("dist/github-snake.svg", results[0]);
fs.writeFileSync("dist/github-snake-brutalist.svg", results[1]);

console.log("Generated dist/github-snake.svg and dist/github-snake-brutalist.svg");
