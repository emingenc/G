import time

def transcribe_words(alignment_data, group_size=3, time_shift=1.0):
    """
    Processes alignment data to group words with adjusted timestamps.

    Args:
        alignment_data (dict): Alignment data from the speech synthesis.
        group_size (int): Number of words per group.
        time_shift (float): Time in seconds to shift the timestamps earlier.

    Returns:
        list: A list of word groups with adjusted timestamps.
    """
    chars = alignment_data['alignment']['characters']
    starts = alignment_data['alignment']['character_start_times_seconds']
    ends = alignment_data['alignment']['character_end_times_seconds']

    words = []
    current_word = ""
    word_start = None
    word_end = None

    for char, start, end in zip(chars, starts, ends):
        if char.strip() == "":
            if current_word:
                words.append({
                    "word": current_word,
                    "start_time": word_start - time_shift,
                    "end_time": word_end - time_shift
                })
                current_word = ""
                word_start = None
                word_end = None
            continue
        if current_word == "":
            word_start = start
        current_word += char
        word_end = end

    # Add the last word if it exists
    if current_word:
        words.append({
            "word": current_word,
            "start_time": word_start - time_shift,
            "end_time": word_end - time_shift
        })

    # Group words based on the specified group size
    grouped_words = [
        words[i:i + group_size]
        for i in range(0, len(words), group_size)
    ]

    return grouped_words

def print_with_timestamps(grouped_words):
    """
    Prints word groups according to their timestamps.

    Args:
        grouped_words (list): List of word groups with timestamps.
    """

    for group in grouped_words:
        print(" ".join([word["word"] for word in group]))
        time.sleep(group[-1]["end_time"] - group[0]["start_time"])
        print(
            f"Start: {group[0]['start_time']:.2f}s, "
            f"End: {group[-1]['end_time']:.2f}s"
        )

