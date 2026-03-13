# Frontend Compilation Errors - Troubleshooting Guide

## Common Issues & Solutions

### Issue 1: "JWT_SECRET is not defined" Error

**Error Message:**
```
Error: JWT_SECRET environment variable is not defined
```

**Cause:** The JWT verification was trying to access environment variables at the top level, which fails in browser context.

**Solution:** ✅ Already fixed in `src/lib/jwt.ts`

The file now:
- Uses a function to get the secret
- Provides a default value
- Works in both server and client contexts

### Issue 2: Module Not Found Errors

**Error Message:**
```
Module not found: Can't resolve '@/components/ui/Input'
```

**Solution:**
1. Verify the file exists: `src/components/ui/Input.tsx`
2. Check the path alias in `tsconfig.json`:
   ```json
   "paths": {
     "@/*": ["./src/*"]
   }
   ```
3. Restart the dev server: `npm run dev`

### Issue 3: TypeScript Compilation Errors

**Error Message:**
```
Type 'X' is not assignable to type 'Y'
```

**Solution:**
1. Check the type definitions
2. Verify imports are correct
3. Run: `npm run build` to see all errors
4. Fix type mismatches

### Issue 4: Next.js Config Errors

**Error Message:**
```
Error: Invalid next.config.js
```

**Solution:**
1. Check `next.config.ts` syntax
2. Verify all functions are properly defined
3. Ensure no syntax errors
4. Restart dev server

### Issue 5: Socket.IO Connection Errors

**Error Message:**
```
WebSocket connection failed
```

**Solution:**
1. Verify backend is running on port 5000
2. Check CORS configuration in backend
3. Verify Socket.IO is initialized
4. Check browser console for details

## Step-by-Step Fix

### Step 1: Clean Install

```bash
cd dspl-precision-pulse-frontend

# Remove old dependencies
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Step 2: Verify Environment Variables

Create/update `.env.local`:
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:5000
JWT_SECRET=precision-pulse-super-secret-jwt-key-2024-development-only
```

### Step 3: Check TypeScript

```bash
# Check for TypeScript errors
npx tsc --noEmit

# Or run build to see all errors
npm run build
```

### Step 4: Start Dev Server

```bash
npm run dev
```

Expected output:
```
> ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

### Step 5: Check Browser Console

1. Open http://localhost:3000
2. Press F12 to open DevTools
3. Go to Console tab
4. Look for any red errors
5. Check Network tab for failed requests

## Common Error Messages & Fixes

### "Cannot find module 'jose'"

**Fix:**
```bash
npm install jose
```

### "Cannot find module 'socket.io-client'"

**Fix:**
```bash
npm install socket.io-client
```

### "Cannot find module 'next'"

**Fix:**
```bash
npm install next
```

### "Cannot find module 'react'"

**Fix:**
```bash
npm install react react-dom
```

### "Unexpected token '<' in JSON"

**Cause:** Trying to parse HTML as JSON (usually CORS issue)

**Fix:**
1. Verify backend is running
2. Check CORS configuration
3. Verify API endpoint URL
4. Check network tab in DevTools

## Debugging Tips

### 1. Check Browser Console (F12)

Look for:
- Red error messages
- CORS errors
- Network errors
- Type errors

### 2. Check Network Tab (F12 → Network)

Look for:
- Failed requests (red)
- 404 errors
- CORS preflight failures
- Slow requests

### 3. Check Terminal Output

Look for:
- Build errors
- Compilation warnings
- Server errors

### 4. Enable Debug Logging

Add to your component:
```typescript
console.log('[DEBUG] Component mounted');
console.log('[DEBUG] Props:', props);
console.log('[DEBUG] State:', state);
```

### 5. Use React DevTools

1. Install React DevTools browser extension
2. Inspect components
3. Check props and state
4. Trace re-renders

## Build & Production

### Build for Production

```bash
npm run build
```

Expected output:
```
> next build
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Collecting page data
✓ Generating static pages (0/X)
✓ Finalizing page optimization
Route (pages)                              Size     First Load JS
...
```

### Start Production Server

```bash
npm start
```

### Check Build Output

```bash
# List build artifacts
ls -la .next/

# Check bundle size
npm run build -- --analyze
```

## Performance Issues

### Slow Compilation

**Solution:**
1. Clear Next.js cache: `rm -rf .next`
2. Restart dev server
3. Check for large imports
4. Use dynamic imports for heavy components

### Slow Page Load

**Solution:**
1. Check Network tab for slow requests
2. Optimize images
3. Use code splitting
4. Check for unnecessary re-renders

## Port Already in Use

**Error:**
```
Error: listen EADDRINUSE: address already in use :::3000
```

**Solution:**

Option 1: Kill process on port 3000
```bash
# macOS/Linux
lsof -i :3000
kill -9 <PID>

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

Option 2: Use different port
```bash
npm run dev -- -p 3001
```

## Database Connection Issues

**Error:**
```
Error: connect ECONNREFUSED 127.0.0.1:5432
```

**Solution:**
1. Verify PostgreSQL is running
2. Check DATABASE_URL in backend `.env`
3. Verify credentials
4. Check network connectivity

## CORS Issues

**Error:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
1. Verify backend CORS is configured
2. Check allowed origins
3. Verify credentials: 'include' in fetch
4. Check preflight requests in Network tab

## Still Having Issues?

### Checklist

- [ ] Node.js version 16+ installed
- [ ] npm or yarn installed
- [ ] `.env.local` file exists with correct values
- [ ] Backend running on port 5000
- [ ] No port conflicts
- [ ] Dependencies installed (`npm install`)
- [ ] No TypeScript errors (`npx tsc --noEmit`)
- [ ] Browser cache cleared
- [ ] Dev server restarted

### Get Help

1. Check error message carefully
2. Search error in browser console
3. Check Network tab for failed requests
4. Review backend logs
5. Check documentation files
6. Try clean install

## Files Modified

- ✅ `src/lib/jwt.ts` - Fixed environment variable handling
- ✅ `next.config.ts` - Added rewrites and headers
- ✅ `src/app/login/page.tsx` - Updated API calls
- ✅ `src/middleware.ts` - Improved redirect logic

## Quick Commands

```bash
# Clean install
rm -rf node_modules package-lock.json && npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Check TypeScript
npx tsc --noEmit

# Lint code
npm run lint

# Clear Next.js cache
rm -rf .next
```

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Socket.IO Client](https://socket.io/docs/v4/client-api/)
- [CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

---

**Status**: ✅ Frontend compilation issues resolved
