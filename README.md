## squish?! 

experimental repository for testing text -> image long-context compression

inspired by 
- DeepSeek-OCR: Contexts Optical Compression https://github.com/deepseek-ai/DeepSeek-OCR/blob/main/DeepSeek_OCR_paper.pdf
- Glyph: Scaling Context Windows via Visual-Text Compression https://arxiv.org/pdf/2510.17800 

Successfully does -50% compression of medium-length haystack tasks (ie. 16k text tokens = 8k image tokens)
  - further optimizations get me a 70k/10k ratio (-86% ish?) not sure tho

## todos:
- why is image slower?
- can you further compress
- proper textwrap framing
- run on OSS model not openai

<img width="860" height="804" alt="image" src="https://github.com/user-attachments/assets/3c0b551f-cfe5-49eb-a0cc-b6372aef0089" />

page:

<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/cbc06e6d-dd23-499b-9a2a-9e376cefb005" />
