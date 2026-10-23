// Trim the raw recording and place Polly narration clips on the planned timeline.
// Usage: node mux.js <case_id>   (reads <case>.timing.json, <case>.lines.json, audio/<case>/lN.mp3)
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const caseId = process.argv[2];
const dir = __dirname;
const timing = JSON.parse(fs.readFileSync(path.join(dir, `${caseId}.timing.json`)));
const linesPath = path.join(dir, `${caseId}.lines.json`);
const lines = fs.existsSync(linesPath) ? JSON.parse(fs.readFileSync(linesPath)) : [];
const out = path.join(dir, `${caseId}.mp4`);

const args = ["-y", "-v", "error", "-i", path.join(dir, `${caseId}.raw.webm`)];
const filters = [`[0:v]trim=start=${timing.trim_s},setpts=PTS-STARTPTS,fps=30,format=yuv420p[v]`];
lines.forEach((line, i) => {
  args.push("-i", path.join(dir, "audio", caseId, `l${i + 1}.mp3`));
  filters.push(`[${i + 1}:a]adelay=${Math.round(line.t * 1000)}:all=1[a${i + 1}]`);
});
if (lines.length) {
  filters.push(`${lines.map((_, i) => `[a${i + 1}]`).join("")}amix=inputs=${lines.length}:normalize=0,aresample=48000,apad[a]`);
}
args.push("-filter_complex", filters.join(";"), "-map", "[v]");
if (lines.length) args.push("-map", "[a]", "-c:a", "aac", "-b:a", "128k");
args.push("-t", String(timing.duration_s), "-c:v", "libx264", "-preset", "slow", "-crf", "20",
  "-pix_fmt", "yuv420p", "-movflags", "+faststart", out);
execFileSync("ffmpeg", args, { stdio: "inherit" });
console.log(out);
