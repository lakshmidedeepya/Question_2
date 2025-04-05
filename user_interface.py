from ngram import NgramCharacterModel
import curses
import re
import sys
import os
from typing import List


class TerminalUI:
    def __init__(self, prediction_model, text_content):
        self.screen = None
        self.suggestions = []
        self.current_suggestion_idx = 0
        self.scores = []
        self.text_content = text_content
        self.user_input = ""
        self.cursor_pos = 0
        self.cursor_row = 1
        self.total_tab_presses = 0
        self.total_letters_typed = 0
        self.total_suggestion_letters = 0

        self.suggestions_panel = None
        self.text_panel = None
        self.input_panel = None
        self.scores_panel = None

        self.prediction_model = prediction_model

    def calculate_scores(self, text: str) -> List[int]:
        """

        Calculate scores as specified on the question document based on current input.
        """
        # TODO: Write the logic for the scores to evaluate your model
        # pass
        total_letters_typed = self.total_letters_typed # Count letters typed
        total_tab_presses = self.total_tab_presses  # Track total Tab key presses
        words = text.split()  # Extract currently typed words


        total_letters_word=sum(1 for char in text if char.isalpha())
        avg_letters_per_word = total_letters_typed / total_letters_word if total_letters_word else total_letters_typed # Avg letters per word
        # avg_tabs_per_word = total_tab_presses / total_words
        avg_tabs_per_word = total_tab_presses / len(words) if words else 0  # Avg tabs per word

        return [total_letters_typed, total_tab_presses, avg_letters_per_word, avg_tabs_per_word]

    def find_last_word_start(self, text: str, cursor_pos: int) -> int:
        """Find the start position of the last word being typed."""
        if cursor_pos == 0:
            return 0

        text_before_cursor = text[:cursor_pos]
        match = re.search(r"[^\s]*$", text_before_cursor)
        if match:
            return cursor_pos - len(match.group(0))
        return cursor_pos

    def get_current_word(self) -> str:
        """Get the current word being typed."""
        word_start = self.find_last_word_start(self.user_input, self.cursor_pos)
        return self.user_input[word_start : self.cursor_pos]

    def replace_current_word(self, new_word: str) -> None:
        """Replace the current word with a suggestion."""
        word_start = self.find_last_word_start(self.user_input, self.cursor_pos)
        self.user_input = (
            self.user_input[:word_start] + new_word + self.user_input[self.cursor_pos :]
        )
        self.cursor_pos = word_start + len(new_word)

    def draw_suggestions_panel(self) -> None:
        """Draw the suggestions panel (top panel)."""
        h, w = self.suggestions_panel.getmaxyx()
        self.suggestions_panel.erase()

        self.suggestions_panel.box()
        self.suggestions_panel.addstr(0, 2, " Suggestions ")

        if not self.suggestions:
            self.suggestions_panel.addstr(1, 2, "No suggestions")
        else:
            display_text = ""
            for i, suggestion in enumerate(self.suggestions):
                if i == self.current_suggestion_idx:
                    display_text += f"[{suggestion}] "
                else:
                    display_text += f"{suggestion} "

            if len(display_text) > w - 4:
                display_text = display_text[: w - 7] + "..."

            self.suggestions_panel.addstr(1, 2, display_text)

        self.suggestions_panel.noutrefresh()

    def draw_text_panel(self) -> None:
        """Draw the text panel (second panel)."""
        h, w = self.text_panel.getmaxyx()
        self.text_panel.erase()

        self.text_panel.box()
        self.text_panel.addstr(0, 2, " Text Content ")

        words = self.text_content.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line + " " + word) > w - 4:
                lines.append(current_line)
                current_line = word
            else:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word

        if current_line:
            lines.append(current_line)

        for i, line in enumerate(lines):
            if i < h - 2:
                self.text_panel.addstr(i + 1, 2, line)

        self.text_panel.noutrefresh()

    def draw_input_panel(self) -> None:
        """Draw the input panel (third panel)."""
        h, w = self.input_panel.getmaxyx()
        self.input_panel.erase()

        self.input_panel.box()
        self.input_panel.addstr(0, 2, " Input ")

        prompt = "> "
        prompt_len = len(prompt)

        available_width = w - 4
        first_line_width = available_width - prompt_len
        
        lines = []
        current_pos = 0
        text = self.user_input
        
        first_line_text = text[:first_line_width] if len(text) > 0 else ""
        lines.append(first_line_text)
        current_pos = len(first_line_text)
        
        while current_pos < len(text) and len(lines) < h - 2:
            next_chunk = text[current_pos:current_pos + available_width]
            lines.append(next_chunk)
            current_pos += len(next_chunk)
        
        for i, line in enumerate(lines):
            if i >= h - 2:
                break
            if i == 0:
                self.input_panel.addstr(i + 1, 2, prompt + line)
            else:
                self.input_panel.addstr(i + 1, 2, line)
        
        cursor_pos = self.cursor_pos
        if current_pos <= first_line_width:
            cursor_y = 1
            cursor_x = 2 + prompt_len + cursor_pos
        else:
            cursor_pos -= first_line_width
            cursor_y = 1 + (cursor_pos // available_width) + 1
            cursor_x = 2 + (cursor_pos % available_width)
            
        cursor_y = min(cursor_y, h - 2)
        cursor_x = min(cursor_x, w - 2)
        
        self.cursor_row = cursor_y
        self.cursor_col = cursor_x
        
        try:
            self.input_panel.move(cursor_y, cursor_x)
        except:
            self.input_panel.move(1, 2 + prompt_len)

        self.input_panel.noutrefresh()

    def draw_scores_panel(self) -> None:
        """Draw the scores panel (bottom panel)."""
        h, w = self.scores_panel.getmaxyx()
        self.scores_panel.erase()

        self.scores_panel.box()
        self.scores_panel.addstr(0, 2, " Scores ")

        # TODO: Set score labels
        score_labels = ["Letters Typed:", "Tab Presses:", "Avg Letters/Word:", "Avg Tabs/Word:"]
        self.scores = self.calculate_scores(self.user_input)

        display_text = " | ".join(
            f"{label} {score}" for label, score in zip(score_labels, self.scores)
        )

        if len(display_text) > w - 4:
            display_text = display_text[: w - 7] + "..."

        self.scores_panel.addstr(1, (w - len(display_text)) // 2, display_text)
        self.scores_panel.noutrefresh()

    def handle_input(self, key) -> bool:
        """Handle user input keys."""
        if key == curses.KEY_RESIZE:
            return True

        if key == 27:
            return False

        if key == 9:
            if self.suggestions:
                
                self.current_suggestion_idx = (self.current_suggestion_idx + 1) % len(
                    self.suggestions
                )
            
                self.total_tab_presses+=1
            return True

        if key == 10:
            current_word = self.get_current_word()
            if self.suggestions and self.current_suggestion_idx < len(self.suggestions):
                
                
                self.replace_current_word(self.suggestions[self.current_suggestion_idx])
                self.suggestions = []
                self.current_suggestion_idx = 0
                #self.total_tab_presses = 0
            self.total_letters_typed+=len(current_word)
            return True

        if key == curses.KEY_BACKSPACE or key == 127 or key == 8:  # Backspace
            if self.cursor_pos > 0:
                self.user_input = (
                    self.user_input[: self.cursor_pos - 1]
                    + self.user_input[self.cursor_pos :]
                )
                self.cursor_pos -= 1
                current_word = self.get_current_word()
                self.suggestions = self.prediction_model.predict_top_words(current_word)
                #self.total_tab_presses = 0
                self.current_suggestion_idx = 0
                self.scores = self.calculate_scores(self.user_input)
            return True

        if key == curses.KEY_LEFT:
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
                current_word = self.get_current_word()
                self.suggestions = self.prediction_model.predict_top_words(current_word)
                self.current_suggestion_idx = 0
                self.total_tab_presses = 0
            return True

        if key == curses.KEY_RIGHT:
            if self.cursor_pos < len(self.user_input):
                self.cursor_pos += 1
                current_word = self.get_current_word()
                self.suggestions = self.prediction_model.predict_top_words(current_word)
                self.current_suggestion_idx = 0
                self.total_tab_presses = 0
            return True
        
        if key == 32:  # Spacebar Key -> Reset scores
            char = chr(key)
            self.user_input = (
                self.user_input[: self.cursor_pos]
                + char
                + self.user_input[self.cursor_pos :]
            )
            
            self.cursor_pos += 1
            #self.total_tab_presses = 0  # Reset Tab key presses
            #self.total_letters_typed = 0  # Reset letter keys typed
            #self.scores = self.calculate_scores(self.user_input)  # Recalculate scores
            return True

        if 32 <= key <= 126:
            char = chr(key)
            self.user_input = (
                self.user_input[: self.cursor_pos]
                + char
                + self.user_input[self.cursor_pos :]
            )
            self.cursor_pos += 1

            current_word = self.get_current_word()
            #self.total_tab_presses = 0
            self.suggestions = self.prediction_model.predict_top_words(current_word)
            self.current_suggestion_idx = 0
            self.scores = self.calculate_scores(self.user_input)

        return True

    def run(self) -> None:
        """Main function to run the terminal UI."""
        try:
            self.screen = curses.initscr()
            curses.noecho()
            curses.cbreak()
            curses.start_color()
            self.screen.keypad(True)

            curses.curs_set(1)

            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)

            max_y, max_x = self.screen.getmaxyx()

            suggestions_height = 3
            text_height = (max_y - 6) // 2
            input_height = (max_y - 6) // 2
            scores_height = 3

            self.suggestions_panel = curses.newwin(suggestions_height, max_x, 0, 0)
            self.text_panel = curses.newwin(text_height, max_x, suggestions_height, 0)
            self.input_panel = curses.newwin(
                input_height, max_x, suggestions_height + text_height, 0
            )
            self.scores_panel = curses.newwin(
                scores_height, max_x, suggestions_height + text_height + input_height, 0
            )

            self.draw_suggestions_panel()
            self.draw_text_panel()
            self.draw_input_panel()
            self.draw_scores_panel()

            self.input_panel.move(1, 4)
            curses.doupdate()

            running = True
            while running:
                try:
                    self.input_panel.move(self.cursor_row, self.cursor_col)
                except:
                    self.input_panel.move(1, 4)
                self.input_panel.noutrefresh()
                curses.doupdate()

                key = self.screen.getch()
                running = self.handle_input(key)

                if key == curses.KEY_RESIZE:
                    max_y, max_x = self.screen.getmaxyx()

                    suggestions_height = 3
                    text_height = (max_y - 6) // 2 + 2
                    input_height = (max_y - 6) // 2 + 1
                    scores_height = 3

                    self.suggestions_panel = curses.newwin(
                        suggestions_height, max_x, 0, 0
                    )
                    self.text_panel = curses.newwin(
                        text_height, max_x, suggestions_height, 0
                    )
                    self.input_panel = curses.newwin(
                        input_height, max_x, suggestions_height + text_height, 0
                    )
                    self.scores_panel = curses.newwin(
                        scores_height,
                        max_x,
                        suggestions_height + text_height + input_height,
                        0,
                    )

                self.draw_suggestions_panel()
                self.draw_text_panel()
                self.draw_input_panel()
                self.draw_scores_panel()

                try:
                    self.input_panel.move(self.cursor_row, self.cursor_col)
                    self.input_panel.noutrefresh()
                except:
                    pass
                curses.doupdate()

        finally:
            if self.screen:
                curses.nocbreak()
                self.screen.keypad(False)
                curses.echo()
                curses.endwin()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python user_interface.py <path_to_corpus_folder/file>")
        sys.exit(1)

    if sys.argv[1].endswith(".txt"):
        corpus_file_path = sys.argv[1]
        try:
            with open(corpus_file_path, "r") as file:
                corpus = file.read()
        except FileNotFoundError:
            print(f"File not found: {corpus_file_path}")
            sys.exit(1)
    else:
        corpus_folder_path = sys.argv[1]
        corpus_file_path_list = sorted(os.listdir(corpus_folder_path))
        corpus_file_path_list = [
            os.path.join(corpus_folder_path, file_path)
            for file_path in corpus_file_path_list
        ]

        corpus = ""

        for corpus_file_path in corpus_file_path_list:
            try:
                with open(corpus_file_path, "r") as file:
                    cur_corpus = file.read()
            except FileNotFoundError:
                print(f"File not found: {corpus_file_path}")
                sys.exit(1)
            corpus += cur_corpus

    n = 5
    model = NgramCharacterModel(corpus, n)

    ui = TerminalUI(model, corpus)
    ui.run()
