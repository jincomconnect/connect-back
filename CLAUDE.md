# CLAUDE.md - Node.js Express/MongoDB Backend

## Commands
- **Start server**: `npm start` or `node server.js`
- **Run tests**: `npm test`
- **Install dependencies**: `npm install`
- **Dev mode with auto-reload**: `npm run dev` (requires nodemon)

## Code Style Guidelines
- **Format**: Use 2-space indentation, no trailing whitespace
- **Imports**: Group by built-in, external, then internal; alphabetize within groups
- **Naming**: camelCase for variables/functions, PascalCase for classes/models
- **Async/Await**: Prefer over callbacks or raw promises
- **Error Handling**: Always use try/catch with async functions
- **Middleware**: Use middleware for common functionality (auth, validation)
- **Environment Variables**: Store secrets in .env file (never commit)
- **Models**: Define clear Mongoose schemas with validation
- **Routes**: Organize endpoints by resource, use Express Router
- **Controllers**: Separate business logic from route definitions

## Security Best Practices
- Always validate and sanitize user inputs
- Use bcrypt for password hashing (never store plaintext)
- Implement proper JWT token validation for authentication