# BookCreator

BookCreator is an AI-powered application that generates complete books using artificial intelligence. Connect with either Anthropic's Claude or OpenAI's GPT models to create customized content.

## Features

- Generate complete books with AI assistance
- Connect to either Anthropic (Claude) or OpenAI (GPT) APIs
- Custom book structure generation
- Chapter-by-chapter content creation with fine-tuned parameters
- Export in multiple formats (Markdown, plain text)
- Save and load projects for future editing

## Requirements

- Python 3.11+
- API key from Anthropic or OpenAI

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/book-creator.git
cd book-creator

# Install dependencies
pip install -r requirements.txt
```

## Usage

1. Set your API keys as environment variables:
   ```bash
   export ANTHROPIC_API_KEY=your_anthropic_key
   export OPENAI_API_KEY=your_openai_key
   ```

2. Launch the application:
   ```bash
   streamlit run app.py
   ```

3. Follow the interface to:
   - Configure your AI provider and model
   - Define your book structure (title, theme, target audience, etc.)
   - Generate and edit content chapter by chapter
   - Export your completed book

## Development

The application is built with:
- Streamlit for the user interface
- Anthropic/OpenAI APIs for content generation
- Python for backend processing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Anthropic's Claude and OpenAI's GPT models
- Created for writers, educators, and content creators looking to leverage AI
