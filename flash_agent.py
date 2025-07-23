import argparse
import json
from pathlib import Path
from collections import defaultdict

class FlashAgent:
    def __init__(self, notes_dir: Path):
        if not notes_dir.exists() or not notes_dir.is_dir():
            raise ValueError(f"Notes directory '{notes_dir}' is invalid")
        self.notes_dir = notes_dir
        self.flashcards = []
        self.log_messages = []
        self._parsed_notes = None

    def parse_notes(self):
        if self._parsed_notes is not None:
            return self._parsed_notes

        headings = defaultdict(list)
        for path in self.notes_dir.rglob('*.md'):
            current_concept = None
            current_content = []
            try:
                lines = path.read_text(encoding='utf-8').splitlines()
            except Exception as e:
                self.log_messages.append(f"Warning: Could not read file {path}: {e}")
                continue
            for line in lines:
                if line.startswith('# '):
                    if current_concept is not None and current_content:
                        headings[current_concept].append('\n'.join(current_content).strip())
                    current_concept = line.lstrip('#').strip()
                    current_content = []
                elif line.startswith('#'):
                    if current_concept is not None and current_content:
                        headings[current_concept].append('\n'.join(current_content).strip())
                    current_content = []
                else:
                    current_content.append(line)
            if current_concept is not None and current_content:
                headings[current_concept].append('\n'.join(current_content).strip())

        self._parsed_notes = headings
        return headings

    def generate_flashcards(self):
        definitions = defaultdict(list)
        ambiguous_concepts = set()
        for concept, sections in self.parse_notes().items():
            for text in sections:
                if concept in definitions and text not in definitions[concept]:
                    ambiguous_concepts.add(concept)
                definitions[concept].append(text)
                self.flashcards.append({'concept': concept, 'definition': text})
        if ambiguous_concepts:
            self.log_messages.append(
                f"Ambiguity detected for the following concepts with differing definitions: {', '.join(sorted(ambiguous_concepts))}."
            )
        return self.flashcards

    def export_json(self, output: Path):
        output.write_text(json.dumps(self.flashcards, indent=2), encoding='utf-8')

    def export_md(self, output: Path):
        with output.open('w', encoding='utf-8') as f:
            for card in self.flashcards:
                f.write(f"### {card['concept']}\n{card['definition']}\n\n")

    def summarize(self):
        summary = {}
        for concept, defs in self.parse_notes().items():
            if defs:
                preview = defs[0]
                summary[concept] = preview[:100] + ('...' if len(preview) > 100 else '')
            else:
                summary[concept] = ''
        return summary

    def print_log(self):
        for msg in self.log_messages:
            print(msg)


def main():
    parser = argparse.ArgumentParser(description='FlashAgent CLI')
    subparsers = parser.add_subparsers(dest='command')

    summarize_parser = subparsers.add_parser('summarize')
    generate_parser = subparsers.add_parser('generate')
    export_parser = subparsers.add_parser('export')

    summarize_parser.add_argument('--notes', default='notes', help='Path to notes directory')
    generate_parser.add_argument('--notes', default='notes', help='Path to notes directory')
    export_parser.add_argument('--notes', default='notes', help='Path to notes directory')

    generate_parser.add_argument('--json', default='flashcards.json', help='Output JSON file')
    generate_parser.add_argument('--md', default='flashcards.md', help='Output Markdown file')
    export_parser.add_argument('--json', default='flashcards.json', help='Output JSON file')
    export_parser.add_argument('--md', default='flashcards.md', help='Output Markdown file')

    args = parser.parse_args()
    agent = FlashAgent(Path(args.notes))

    if args.command == 'summarize':
        summary = agent.summarize()
        print(json.dumps(summary, indent=2))
    elif args.command == 'generate':
        agent.generate_flashcards()
        agent.print_log()
        print(json.dumps(agent.flashcards, indent=2))
    elif args.command == 'export':
        agent.generate_flashcards()
        agent.export_json(Path(args.json))
        agent.export_md(Path(args.md))
        agent.print_log()
        print(f"Exported {len(agent.flashcards)} flashcards to {args.json} and {args.md}")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
