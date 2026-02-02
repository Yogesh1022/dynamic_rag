# RAG Dashboard - React Frontend

React-based dashboard for the FastAPI RAG system powered by Llama3.

## Features

- 💬 **Chat Interface** - Interactive chat with RAG retrieval and source citations
- 📄 **Document Management** - Upload, view, and delete documents
- 📊 **Dashboard** - System metrics and status overview
- 🔍 **Hybrid Search** - Vector + BM25 keyword search
- ⚙️ **Configurable Settings** - Adjust model, temperature, and retrieval parameters

## Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend server running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The dashboard will be available at http://localhost:3000

### Build for Production

```bash
# Build static files
npm run build

# Preview production build
npm run preview
```

## Configuration

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
dashboard/
├── src/
│   ├── api/
│   │   └── client.js          # API client for backend
│   ├── pages/
│   │   ├── ChatPage.jsx       # Chat interface
│   │   ├── DocumentsPage.jsx  # Document management
│   │   ├── ConversationsPage.jsx  # Chat history
│   │   └── DashboardPage.jsx  # System dashboard
│   ├── App.jsx                # Main app component
│   ├── main.jsx               # Entry point
│   └── index.css              # Global styles
├── index.html
├── package.json
└── vite.config.js
```

## Features in Detail

### Chat Page
- Real-time chat with Llama3
- Source citations from retrieved documents
- Conversation history
- Configurable settings (model, temperature, top_k)
- Hybrid search toggle

### Documents Page
- Drag-and-drop file upload
- Support for PDF, PNG, JPG, JPEG, TIFF
- Document status tracking (processing, completed, failed)
- Delete documents
- View chunks count

### Dashboard Page
- System health status
- Document statistics
- Recent documents preview
- System information (models, search method, etc.)

## API Integration

The dashboard communicates with the FastAPI backend via REST API:

- `POST /api/v1/chat` - Send chat messages
- `POST /api/v1/documents/upload` - Upload documents
- `GET /api/v1/documents/` - List documents
- `DELETE /api/v1/documents/{id}` - Delete document
- `GET /health` - Health check

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

### Technologies Used

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Lucide React** - Icon library

## Troubleshooting

### Backend Connection Error
Make sure the FastAPI server is running:
```bash
cd ..
uvicorn app.main:app --reload
```

### Ollama Not Available
Start Ollama and pull Llama3:
```bash
ollama serve
ollama pull llama3
```

### Upload Fails
Check:
1. File size < 10MB
2. File type is supported (PDF, PNG, JPG, JPEG, TIFF)
3. Backend server is running
4. Upload directory exists and is writable

## License

Part of the Industry-Grade FastAPI RAG System project.
