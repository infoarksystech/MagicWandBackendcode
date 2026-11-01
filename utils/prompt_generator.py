def generate_multi_panel_prompts(base_prompt: str, scene_elements: list, style: str = "consistent"):
    """
    Generate multiple panel prompts (e.g., for a diptych, triptych, quad, etc.)

    Parameters:
        base_prompt (str): The shared base scene and style.
        scene_elements (list): List of unique descriptions for each panel (left to right).
        style (str): Optional styling note ("consistent", "complementary", etc.)

    Returns:
        List of prompts (one per panel).
    """
    prompts = []
    total = len(scene_elements)

    for i, description in enumerate(scene_elements):
        if total == 2:
            panel_label = "left" if i == 0 else "right"
        elif total == 3:
            panel_label = ["left", "center", "right"][i]
        else:
            panel_label = f"panel {i + 1}"

        panel_prompt = (
            f"{base_prompt} — {panel_label} panel: "
            f"{description.strip().capitalize()}. Ensure the design matches the overall style and color scheme for visual harmony."
        )

        if style != "consistent":
            panel_prompt += f" The panel should be styled to be {style} with the others."

        prompts.append(panel_prompt)

    return prompts