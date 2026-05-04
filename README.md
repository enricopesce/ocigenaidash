# OCI GenAI Agents Demo

A Streamlit application that provides an AI assistant specialized in environmental regulations and waste management, powered by Oracle Cloud Infrastructure (OCI) Generative AI Agents.

## Features

- 🧠 **AI-Powered Chat** - Interactive chat interface with OCI GenAI Agent
- 🎯 **Preset Questions** - Quick access to common environmental regulation queries
- 📚 **RAG Document Matches** - Compact document, page, source excerpt, and source-link display
- 💬 **Chat History** - Persistent conversation history during session
- 🌐 **Document Access** - Direct links to source documents

## Prerequisites

- Python 3.12
- Oracle Cloud Infrastructure (OCI) account
- OCI GenAI Agent configured and deployed

## Installation

1. **Clone or download the project**
   ```bash
   git clone <your-repo-url>
   cd oci-genai-demo
   ```

2. **Create a virtual environment**
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

## Configuration

This application continues to use OCI Generative AI Agents Runtime through `GenerativeAiAgentRuntimeClient`; it does not call the direct OCI Generative AI inference APIs.

### 1. OCI Configuration

Create an OCI configuration file at `~/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1..your-user-ocid
fingerprint=your-fingerprint
tenancy=ocid1.tenancy.oc1..your-tenancy-ocid
region=eu-frankfurt-1
key_file=~/.oci/your-private-key.pem
```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
OCI_AGENT_ENDPOINT_ID=your-agent-endpoint-id
OCI_SERVICE_ENDPOINT=https://agent-runtime.generativeai.eu-frankfurt-1.oci.oraclecloud.com

# Optional citation URL rewrite settings
OS_URL=https://objectstorage\.eu-frankfurt-1\.oraclecloud\.com
OS_URL_PREAUTH=https://your-replacement-url.com
```


## Running the Application

1. **Start the Streamlit app**
   ```bash
   streamlit run app.py
   ```

2. **Access the application**
   - Open your browser to `http://localhost:8501`

## Project Structure

```
oci-genai-demo/
├── app.py              # Main application file
├── .env                # Environment variables (create this)
├── requirements.txt    # Runtime Python dependencies
├── requirements-dev.txt # Local test dependencies
├── README.md          # This file
└── .gitignore         # Git ignore file (recommended)
```

## Dependencies

Runtime dependencies are declared in `requirements.txt`.

For local tests, install:

```bash
python -m pip install -r requirements-dev.txt
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `OCI_AGENT_ENDPOINT_ID` | ✅ Yes | Your OCI GenAI Agent endpoint ID |
| `OCI_SERVICE_ENDPOINT` | ✅ Yes | OCI GenAI service endpoint URL |
| `OS_URL` | No | Regex pattern for URL replacement in citations |
| `OS_URL_PREAUTH` | No | Replacement URL for document access |

If `OS_URL_PREAUTH` is empty, the app keeps OCI citation URLs unchanged.

## Getting Your OCI Agent Endpoint ID

1. Log in to OCI Console
2. Navigate to **AI Services** → **Generative AI Agents**
3. Select your agent
4. Copy the **Agent Endpoint ID** from the details page

## Running the Application

### Local Development
```bash
streamlit run app.py
```

### Production Mode
For production-like local deployment:
```bash
streamlit run app.py --server.port=8501 --server.headless=true
```

### Background Process
To run in background:
```bash
nohup streamlit run app.py > streamlit.log 2>&1 &
```

### Different Port
To run on a different port:
```bash
streamlit run app.py --server.port=8080
```

### Cloud Deployment (Optional)
- **Streamlit Cloud**: Push to GitHub and connect via streamlit.io
- **Direct server deployment**: Copy files to server and run locally

## Customization

### Adding New Preset Questions
Edit the `PRESET_QUESTIONS` list in `app.py`:

```python
PRESET_QUESTIONS = [
    "Your new question here",
    "Another question",
    # ... existing questions
]
```

### Modifying the UI
The app uses standard Streamlit components. Customize by:
- Changing page configuration in `st.set_page_config()`
- Modifying titles and descriptions
- Adding custom CSS with `st.markdown()`

### Citation URL Replacement
Modify `OS_URL` and `OS_URL_PREAUTH` to customize how document URLs are transformed for user access.

## Troubleshooting

### Common Issues

1. **"OCI_AGENT_ENDPOINT_ID environment variable is required"**
   - Check your `.env` file exists and contains the correct endpoint ID

2. **"Failed to initialize OCI client"**
   - Verify your `~/.oci/config` file is correctly configured
   - Ensure your private key file exists and has correct permissions

3. **Authentication errors**
   - Check your OCI credentials and permissions
   - Verify your user has access to the GenAI Agent service


### Debug Mode
To enable detailed logging, add to your `.env`:
```env
DEBUG_MODE=true
```

## Security Considerations

- Keep your `.env` file secure and never commit it to version control
- Use strong passwords and rotate them regularly
- Ensure your OCI credentials have minimal required permissions
- Consider implementing additional authentication for production use

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues related to:
- **OCI GenAI Agents**: Check OCI documentation and support
- **This application**: Create an issue in the project repository
- **Streamlit**: Visit streamlit.io documentation

---

**Happy coding! 🚀**
