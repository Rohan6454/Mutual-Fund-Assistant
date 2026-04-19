// Client-side API fetching utilities

export interface Thread {
  thread_id: string;
  title?: string;
  created_at?: string;
}

export interface Message {
  role: 'user' | 'assistant';
  text: string;
}

const DEFAULT_API_BASE = "http://localhost:8000";

export class ApiService {
  private static getBaseUrl(): string {
    // In browser context we could check localStorage, otherwise fallback
    if (typeof window !== 'undefined') {
      const storedUrl = localStorage.getItem('api_base_url');
      if (storedUrl) return storedUrl;
    }
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }

  static setBaseUrl(url: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('api_base_url', url);
    }
  }

  static async getThreads(): Promise<Thread[]> {
    const url = `${this.getBaseUrl().replace(/\/$/, '')}/api/threads`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch threads");
    const data = await res.json();
    return data.threads || [];
  }

  static async createThread(): Promise<string> {
    const url = `${this.getBaseUrl().replace(/\/$/, '')}/api/threads`;
    const res = await fetch(url, { method: "POST" });
    if (!res.ok) throw new Error("Failed to create thread");
    const data = await res.json();
    return data.thread_id;
  }

  static async deleteThread(threadId: string): Promise<void> {
    const url = `${this.getBaseUrl().replace(/\/$/, '')}/api/threads/${threadId}`;
    const res = await fetch(url, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete thread");
  }

  static async getThreadMessages(threadId: string): Promise<Message[]> {
    const url = `${this.getBaseUrl().replace(/\/$/, '')}/api/threads/${threadId}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch messages");
    const data = await res.json();
    return data.messages || [];
  }

  static async sendMessage(message: string, threadId: string | null): Promise<{thread_id: string, answer: string}> {
    const url = `${this.getBaseUrl().replace(/\/$/, '')}/api/chat`;
    const payload = { message, thread_id: threadId };
    
    // Default 60s timeout for chat to handle cold starts
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);
    
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Chat API error: ${res.status} - ${errorText}`);
      }
      
      const data = await res.json();
      return {
         thread_id: data.thread_id,
         answer: data.answer || '' 
      };
    } catch (e: any) {
      clearTimeout(timeoutId);
      if (e.name === 'AbortError') {
        throw new Error("The service is taking a while to wake up. Please try again in 15-20 seconds.");
      }
      throw e;
    }
  }
}
