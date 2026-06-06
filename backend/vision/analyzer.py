import base64
import json
import logging
from groq import Groq
from core.config import settings
from vision.screen import take_screenshot, capture_active_window
from tools.registry import registry

logger = logging.getLogger("AlchemistVisionAnalyzer")

def _encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def _analyze_image(image_path: str, prompt: str) -> str:
    logger.info(f"Analyzing image {image_path} with prompt: {prompt}")
    try:
        base64_image = _encode_image(image_path)
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        response = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            temperature=0.1
        )
        result = response.choices[0].message.content
        logger.info("Successfully analyzed image.")
        return result
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return f"Failed to analyze image: {e}"

def analyze_screen() -> str:
    """Takes a full screenshot and returns a structured JSON observation."""
    logger.info("Executing analyze_screen tool")
    screenshot_result = take_screenshot()
    if "Failed" in screenshot_result:
        return screenshot_result
        
    image_path = screenshot_result.split("saved to ")[-1].strip()
    
    prompt = """
    Analyze this screen and return a strictly formatted JSON object exactly like this example:
    {
        "applications": ["App 1", "App 2"],
        "visible_text": ["Important text 1", "Important text 2"],
        "buttons": ["Submit", "Cancel"],
        "errors": ["File not found", "Network timeout"],
        "summary": "A brief summary of what is on the screen."
    }
    Return ONLY the JSON. Do not include markdown code blocks.
    """
    logger.info(f"Using screenshot path: {image_path}")
    analysis = _analyze_image(image_path, prompt)
    
    # Try to clean up if the model wrapped it in markdown anyway
    analysis = analysis.strip()
    if analysis.startswith("```json"):
        analysis = analysis[7:]
    if analysis.endswith("```"):
        analysis = analysis[:-3]
        
    try:
        # Validate JSON parses correctly
        json.loads(analysis.strip())
    except json.JSONDecodeError:
        logger.error(f"Failed to parse vision JSON: {analysis}")
        
    logger.info(f"Vision Analysis Output: {analysis.strip()}")
    return analysis.strip()

def read_screen_text() -> str:
    """Takes a full screenshot and performs OCR to extract all visible text."""
    logger.info("Executing read_screen_text tool")
    screenshot_result = take_screenshot()
    if "Failed" in screenshot_result:
        return screenshot_result
        
    image_path = screenshot_result.split("saved to ")[-1].strip()
    
    prompt = "Read all the text visible in this image. Output only the exact text you see, preserving layout as much as possible."
    logger.info(f"Using screenshot path: {image_path}")
    ocr_result = _analyze_image(image_path, prompt)
    logger.info(f"OCR Output: {ocr_result}")
    return ocr_result

def identify_active_window() -> str:
    """Captures the active window and analyzes it."""
    logger.info("Executing identify_active_window tool")
    screenshot_result = capture_active_window()
    if "Failed" in screenshot_result:
        return screenshot_result
        
    image_path = screenshot_result.split("saved to ")[-1].strip()
    
    prompt = "Identify the application shown in this image and briefly summarize what is currently happening in it (e.g., error messages, dialog boxes, content)."
    return _analyze_image(image_path, prompt)

# Register Tools
registry.register("analyze_screen", analyze_screen)
registry.register("read_screen_text", read_screen_text)
registry.register("identify_active_window", identify_active_window)
