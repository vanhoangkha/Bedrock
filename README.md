# Overview Stock-Assistant
This is a simple demo of Amazon Bedrock and Anthropic Claude 3 Sonnet model with langchain and streamlit. For more detail please reference the following link: <br />
- <a href="https://aws.amazon.com/bedrock/" target="_blank">https://aws.amazon.com/bedrock/ </a>
- <a href="https://www.anthropic.com/news/claude-3-family" target="_blank">Claude 3 </a>
# To view demo and sample data:
    Access folder demo for demo video
    Access folder samples for sample videos

# To Setup
Setup <a href='https://docs.python-guide.org/starting/install3/linux/' target='_blank'> Python <a><br />
Setup <a href='https://docs.python-guide.org/starting/install3/linux/' target='_blank'> Python Env<br />
Setup <a href='https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html' target='_blank'> AWS CLI<br />
> git clone<br />
> git pull <br />
> cd stock-assistant <br />
> pip3 install -r requirements.txt <br />
> streamlit run main.py --server.port 8501 <br />

# Architecture
![Architecture](./architecture.png)

# Learn more about prompt and Claude 3
<a href="https://docs.anthropic.com/claude/docs/introduction-to-prompt-design" target="_blank">Introduction to prompt design </a>
<a href="https://www-cdn.anthropic.com/de8ba9b01c9ab7cbabf5c33b80b7bbc618857627/Model_Card_Claude_3.pdf">Model Card</a>

# Demo

## A Simple Chat 
[![Chat](http://img.youtube.com/vi/PdX7i0A4a-M/0.jpg)](https://www.youtube.com/watch?v=PdX7i0A4a-M)]

## Questions and Anwsers
[![Questions and Anwsers](http://img.youtube.com/vi/ciJfAhyRjTI/0.jpg)](https://www.youtube.com/watch?v=ciJfAhyRjTI)]

## Summary a Lecture
[![Summary](http://img.youtube.com/vi/5JpeWmbHMi0/0.jpg)](https://www.youtube.com/watch?v=5JpeWmbHMi0)]

## Create Multi Choice Questions
[![Create Multi Choice Questions](http://img.youtube.com/vi/AE9gj19a9t0/0.jpg)](https://www.youtube.com/watch?v=AE9gj19a9t0)]

## Suggest a Better Writing
[![Suggest Better Writing](http://img.youtube.com/vi/7xBR5rtcp30/0.jpg)](https://www.youtube.com/watch?v=7xBR5rtcp30)]


## Docker
```
    git pull
    docker compose up -d
```

## Environment
create ```.env``` file
```
    AWS_DEFAULT_REGION=us-east-1
    AWS_ACCESS_KEY_ID=your_access_key
    AWS_SECRET_ACCESS_KEY=your_secret_key
```