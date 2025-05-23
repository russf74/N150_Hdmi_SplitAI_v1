def clean_text(text: str, input_filename="clean_text_input.txt", output_filename="clean_text_output.txt") -> str:
    # Save input text
    with open(input_filename, "w") as f:
        f.write(text)
    # (No cleaning for now)
    cleaned_text = text
    # Save output text
    with open(output_filename, "w") as f:
        f.write(cleaned_text)
    return cleaned_text