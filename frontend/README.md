# Constitution Assistant — Frontend

React 19 SPA for querying the Constitution of Nepal.

Built with Vite 8, Tailwind CSS v4, and React Router.

## Quick Start

```powershell
cd frontend
npm install
npm run dev     # Dev server with HMR at http://localhost:5173
npm run build   # Production build to dist/
npm run lint    # ESLint (flat config)
```

## Pages

| Route | Page | Access |
|-------|------|--------|
| `/` | Home — search bar, results, LLM toggle | Requires login |
| `/history` | Chat history — paginated Q&A list | Requires login |
| `/history/:id` | Single message detail with articles | Requires login |
| `/login` | Login form | Public |
| `/register` | Registration form | Public |
| `/about` | About the project | Public |
| `/how-it-works` | Explanation of the system | Public |
| `*` | 404 Not Found | Public |

## Key Libraries

- React 19, React Router 7
- Tailwind CSS v4 (Vite plugin, no PostCSS config)
- ESLint flat config
