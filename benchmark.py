from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import base64
import dotenv
import json
import openai
import os
import textwrap
import time

openai.api_key = os.getenv("OPENAI_API_KEY")
dotenv.load_dotenv()

model = "gpt-4.1-mini"


def prompt_model(messages) -> str:
    response = openai.chat.completions.create(
        messages=messages,
        model=model,
    )
    content = response.choices[0].message.content
    usage = response.usage
    print(f"Usage: {usage.prompt_tokens} prompt tokens, {usage.completion_tokens} completion tokens, {usage.total_tokens} total tokens")
    return content


def prepare_image(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_image}"


def format_text(text: str) -> str:
    return text.replace("\n", " ").replace("\t", " ").replace("  ", " ")


def path_to_image(path: str, output_dir: str = "images") -> tuple[list[Image.Image], str]:
    data = {}
    with open(path, "r") as file:
        text = file.read()

    text = format_text(text)

    # glyph paper recc
    w, h = 1024, 1024
    mx, my = 10, 10
    font = ImageFont.truetype("Verdana.ttf", 9)
    line_spacing = 6

    Path(output_dir).mkdir(exist_ok=True)

    max_w, max_h = w - (2 * mx), h - (2 * my)
    avg_char_width = font.getlength("x")
    chars_per_line = int(max_w / avg_char_width)
    wrapped_text = textwrap.fill(text, width=chars_per_line)
    lines = wrapped_text.split("\n")
    bbox = font.getbbox("Ay")
    line_height = bbox[3] - bbox[1] + line_spacing
    lines_per_page = int(max_h / line_height)

    text_pages = []
    pages = []
    for i in range(0, len(lines), lines_per_page):
        page_lines = lines[i:i + lines_per_page]
        page_text = "\n".join(page_lines)

        image = Image.new("RGB", (w, h), "white")
        draw = ImageDraw.Draw(image)

        draw.multiline_text(
            xy=(mx, my),
            text=page_text,
            fill="black",
            font=font,
            spacing=line_spacing,
            align="left",
        )

        page_num = len(pages) + 1
        image.save(f"{output_dir}/page{page_num}.jpg")
        data[page_num] = len(page_text)
        pages.append(image)
        text_pages.append(page_text)
    with open("pages.json", "w") as file:
        json.dump(data, file, indent=4)

    return pages, text_pages


pages, text_pages = path_to_image("yule.txt")
print(f"Generated {len(pages)} pages in images/ folder")

n_pages_loaded = 5

questions = [
    "How does the baron describe the painter in the context of his daughter marrying him?",
    "What is Joseph described as wearing when with Madonna?",
    "Describe the Baron's provisions",
    "What did Wilhelm have in his mouth?",
    "I should have liked to have made him a ____; but",
]

system = {"role": "system", "content": "You will be given a long-context document and a question. You must answer the question based on what you read."}


def process_question(question_text: str, question_idx: int) -> dict:
    print(
        f"Processing question {question_idx + 1}/{len(questions)}: {question_text}")

    result = {
        "question": question_text,
        "text_prompt": {},
        "image_prompt": {}
    }

    question = {"role": "user", "content": question_text}

    # text prompt
    try:
        start_time = time.time()
        text_prompt = {"role": "user", "content": "\n".join(
            text_pages[:n_pages_loaded])}
        answer = prompt_model([system, text_prompt, question])
        end_time = time.time()

        result["text_prompt"] = {
            "answer": answer,
            "time_seconds": end_time - start_time,
        }
        print(f"Text prompt completed in {end_time - start_time:.2f}s")
    except Exception as e:
        result["text_prompt"] = {
            "error": str(e)
        }
        print(f"Text prompt failed: {e}")

    # image prompt
    try:
        start_time = time.time()
        image_content = [{
            "type": "image_url",
            "image_url": {
                "url": prepare_image(page),
                "detail": "high",
            },
        } for page in pages[:n_pages_loaded]]
        image_prompt = {"role": "user", "content": image_content}
        answer = prompt_model([system, image_prompt, question])
        end_time = time.time()

        result["image_prompt"] = {
            "answer": answer,
            "time_seconds": end_time - start_time,
            "n_pages": n_pages_loaded
        }
        print(f"Image prompt completed in {end_time - start_time:.2f}s")
    except Exception as e:
        result["image_prompt"] = {
            "error": str(e)
        }
        print(f"Image prompt failed: {e}")

    return result


results = []
with ThreadPoolExecutor(max_workers=min(len(questions), 5)) as executor:
    futures = [
        executor.submit(process_question, q, i)
        for i, q in enumerate(questions)
    ]
    for future in futures:
        results.append(future.result())

output = {
    "model": model,
    "n_pages_loaded": n_pages_loaded,
    "total_pages": len(pages),
    "results": results
}

with open("results.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\n{'='*60}")
print(f"Results saved to results.json")
print(f"{'='*60}")
