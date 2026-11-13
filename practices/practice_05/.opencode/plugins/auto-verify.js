import { spawn } from "node:child_process"

export default (async ({ $, project }) => {
  return {
    "tool.execute.after": async (input, output) => {
      // Run verification after edits. Non-blocking; capture output to tool_output channel.
      try {
        const proc = spawn("python3", ["scripts/verify.py"], { cwd: project.directory })
        let out = ""
        let err = ""
        proc.stdout.on("data", (d) => (out += d.toString()))
        proc.stderr.on("data", (d) => (err += d.toString()))
        proc.on("close", (code) => {
          $.tool_output?.(out || "(no output)")
          if (err) $.tool_output?.("[verify stderr]\n" + err)
          if (code !== 0) {
            $.tool_output?.(`verify.py exited with code ${code}`)
          }
        })
      } catch (e) {
        $.tool_output?.("auto-verify failed: " + (e?.message || String(e)))
      }
    }
  }
})
