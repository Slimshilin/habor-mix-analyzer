Initiate a directory with the name `benchmark-task`. Write down the key files in detail. Put your analysis in an `task_agent_inspection.md` file and add things there as we iterate. You are going to inspect a task and its corresponding agent failure trajectories to analyze the task's difficulty and agent bottlenecks.

In your write up, introduce the task. Review the agent trajectories from docent links to see why agent fails. Initiate subagents to look at each agent trajectory and give you the key messages and observations. Remember to inspect all available agent trajectories - NO SAMPLING ALLOWED!

As you inspect, pay attention to the following things:
1. How close are agents to successfully completing the task. Describe concrete agent behaviors that failed the tests. Show what's expected and what the agents produced - then in what ways (e.g., show me the corresponding test code snippet) that the agents fail the task.

2. How different agent-model behaviors vary and if there are consistent and/or conclusive patterns. Are they showing similar approaches and failing at the same place? Observe both exact actions as well as the number of steps and iterations. Look at both reasoning parts and action spaces. There might be "superficial cause" and "root cause" when you analyze agent failures: for example, on the surface it might be that the agent is writing some wrong command or file/function name; however, if you dive deep to conduct a closer analysis, it might be that the agent didn't fully explore and understand the codebase before execusion that yield this trivial mistake - so the root case is "insufficient understanding, exploration, and reasoning of the environment" rather than a simple "string mismatch". You should clearly analyze the superficial and root causes when you answer this question. Group agent and model behaviors as you explore, and make sure you covered all agent-model combinataions. Expectedly, there might be common bottlenecks where all agents are facing in this task, wherease different agent harnesses and/or models are expected to somewhat show different behaviors. Please write them in detail so that afterwards we can aggregrate per-task detailed analysis to conclude general patterns across tasks.

3. Note that the oracle solution is a rough reference - you shouldn't take it as the "only" and "perfect way to resolve the task - it's just a material for you to check the quality and understand the task instructions, envs, and tests. If you find the task to be broken, note them as well.

4. There might be explicit and implicit instruction. Explicit task instructions are documented in `instruction.md`; however, if domain knowledge and/or exploration of the environment could reveal more information required to complete the task, and they are all expectedly accessible from the environment, then they are considered "implicit instrcitons". You should clearly and carefully identify cases where agents only follow the explicit instructions but ignore or are insufficiently capable of exploring and following the implicit instructions.

5. Imagine what a super capable being would resolve this task, given the current instructions and environment. This may help you better understand and analyze roomhead for agents to improve. Feel free to write down sentences like "If the agents do X more than / instead of doing y like now, they would have resolved the task."

6. Is there any agent hacking happening? How? Did hacking make the agent correct or it actually led the agents towards a wrong direction?


Besides your `task_agent_inspection.md` (should discuss the things above as detailed as possible), you should also write the `task_agent_inspection.json` file with the following format to keep your inspections in a structured way:

```json
{
  "task": {
    "id": "<task-name>",
    "benchmark": "<benchmark-name>",
    "resolved_rate": "A float in [0, 1], showing mean resolved rate of the task across agent-models.",
    "task_broken": false,
    "broken_reason": null
  },

  "headline_finding": "Overall several-sentence findings of agent failures and bottlenecks on this task",

  "common_bottlenecks": [
    "which agent-model(s): what behavior that reveals what bottleneck",
  ],

  "interesting_behaviors":[
    "Which agent-model(s): what consistent and/or interesting behavior that's worth noting; can be interesting in itself and/or comparing to others.",
  ],

  "trajectories": [
    {
      "id": "<docent-run-id>",
      "harness": "terminus-2|claude-code|codex|gemini-cli",
      "model": "claude-opus-4-7|...",
      "outcome": "reward=0 (if unit tests, also show x/y passed)",
      "docent_link": "https://...",
      "superficial_cause": "Detailed reasons specific to the task",
      "root_cause": "High-level root cause of failure pattern",
      "hacking": "none|<exact approach how agent hacks>"
    },
  ]
}
```

The json should note the most important metadata of your analysis. Although full information is detailed docmented in the markdown, the json should serve as a "take-away" metadata that covers all intersting, useful, snd insightful information from your analysis.

KEY RULES TO FOLLOW:
1. Don't be lazy. Read all instructions and digest them carefully. Inspect all trajectories without skipping or guessing. Write down things as detailed as possible.
2. Use subagents smartly to save context and time.
3. Be careful, skeptical, and critical. Ask yourself "why" along with your analysis. Challenge yourself to ensure you arrive at a correct, precise, and concise conclusion. You can even initiate a challenger/critic subagent to challenge yourself and your other subagents to ensure the findings are double-checked and debatedly verified.
4. Stay honest. No hallucination. No guessing. No "likely", "seems", "appears" or similar wording - use concrete evidences and exact examples to demonstrate.

