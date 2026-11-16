# Ecosystem

```text
                    +-----------------------------+
                    |  prompt-to-robot-actions    |
                    |  NL → tools → robot stack   |
                    +-------------+---------------+
                                  |
          +-----------------------+-----------------------+
          |                       |                       |
          v                       v                       v
 aws-bedrock-robotics-demo   robot-vision-dashboard   ai-engineering-lab
 Bedrock-focused demos       Vision / UI experiments  Broader AI practice
```

| Repo | Role |
|------|------|
| **prompt-to-robot-actions** | Core agent + backends + safety + logs |
| [aws-bedrock-robotics-demo](https://github.com/Lazaro549/aws-bedrock-robotics-demo) | AWS Bedrock robotics experiments |
| [robot-vision-dashboard](https://github.com/Lazaro549/robot-vision-dashboard) | Vision / monitoring UI |
| [ai-engineering-lab](https://github.com/Lazaro549/ai-engineering-lab) | Learning lab |

Keep shared concepts aligned: tool schemas, prompt → action, evaluation logs.
