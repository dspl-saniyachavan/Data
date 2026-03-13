import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:5000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password } = body;

    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password required' },
        { status: 400 }
      );
    }

    // Call backend API for authentication
    const response = await axios.post(
      `${BACKEND_URL}/api/auth/login`,
      { email, password },
      { timeout: 5000 }
    );

    return NextResponse.json(response.data, { status: 200 });
  } catch (error: any) {
    const message = error.response?.data?.error || error.message || 'Authentication failed';
    return NextResponse.json(
      { error: message },
      { status: error.response?.status || 401 }
    );
  }
}
