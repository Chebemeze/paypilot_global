'use client';

import Layout from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Icons } from '@/components/icons';
import { useState, useRef, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  evidence?: string[];
  actions?: string[];
  timestamp: string;
}

export default function CopilotPage() {
  const { isLoading: authLoading, user, logout } = useAuth();
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const quickQuestions = [
    'Can we run payroll today?',
    'Who is not ready?',
    'Which employees are high risk?',
    'Which currency wallet is short?',
  ];

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const askQuestion = async (q: string) => {
    if (!q.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: q,
      timestamp: new Date().toISOString(),
    };

    setChatHistory(prev => [...prev, userMessage]);
    setQuestion('');
    setIsLoading(true);

    try {
      const { data } = await api.post('/copilot/query', { question: q });
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer || 'I could not find an answer to that question.',
        evidence: data.evidence,
        actions: data.actions,
        timestamp: new Date().toISOString(),
      };

      setChatHistory(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error(err);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      conversation: chatHistory,
      summary: {
        total_messages: chatHistory.length,
        user_messages: chatHistory.filter(m => m.role === 'user').length,
        assistant_messages: chatHistory.filter(m => m.role === 'assistant').length,
      },
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `copilot-chat-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClearChat = () => {
    if (confirm('Are you sure you want to clear the chat history?')) {
      setChatHistory([]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion(question);
    }
  };

  if (authLoading) {
    return (
      <Layout user={user} onLogout={logout}>
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={logout}>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-2xs font-black text-brand uppercase tracking-widest">
              AI Assistant
            </p>
            <h1 className="text-3xl font-bold text-ink mt-1">Payroll Copilot</h1>
            <p className="text-text-muted mt-1">
              Deterministic answers from your payroll data — zero hallucinations
            </p>
          </div>
          <div className="flex gap-3">
            {chatHistory.length > 0 && (
              <>
                <Button variant="secondary" onClick={handleExport}>
                  <Icons.download className="mr-2" size={16} />
                  Export
                </Button>
                <Button variant="secondary" onClick={handleClearChat}>
                  <Icons.trash className="mr-2" size={16} />
                  Clear
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Quick Questions */}
        <Card>
          <div className="flex flex-wrap gap-2">
            {quickQuestions.map((q) => (
              <Button
                key={q}
                variant="secondary"
                size="sm"
                onClick={() => askQuestion(q)}
                disabled={isLoading}
              >
                {q}
              </Button>
            ))}
          </div>
        </Card>

        {/* Chat History */}
        {chatHistory.length > 0 && (
          <div className="space-y-4">
            {chatHistory.map((message) => (
              <div key={message.id}>
                {message.role === 'user' ? (
                  // User Message
                  <div className="flex justify-end">
                    <div className="max-w-2xl bg-brand text-white rounded-2xl rounded-br-sm px-6 py-4">
                      <p className="text-sm">{message.content}</p>
                      <p className="text-xs opacity-70 mt-2">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ) : (
                  // Assistant Message
                  <div className="flex justify-start">
                    <div className="max-w-2xl space-y-3">
                      <div className="bg-canvas-subtle rounded-2xl rounded-bl-sm px-6 py-4">
                        <p className="text-sm text-ink">{message.content}</p>
                        <p className="text-xs text-text-muted mt-2">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </p>
                      </div>

                      {/* Evidence */}
                      {message.evidence && message.evidence.length > 0 && (
                        <Card>
                          <div className="flex items-start gap-2">
                            <Icons.chart className="text-brand flex-shrink-0 mt-0.5" size={16} />
                            <div className="flex-1">
                              <p className="text-xs font-bold text-brand uppercase tracking-wider mb-2">
                                Evidence
                              </p>
                              <ul className="space-y-1">
                                {message.evidence.map((e, i) => (
                                  <li key={i} className="text-xs text-text-body">
                                    • {e}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </Card>
                      )}

                      {/* Actions */}
                      {message.actions && message.actions.length > 0 && (
                        <Card>
                          <div className="flex items-start gap-2">
                            <Icons.check className="text-success flex-shrink-0 mt-0.5" size={16} />
                            <div className="flex-1">
                              <p className="text-xs font-bold text-success uppercase tracking-wider mb-2">
                                Recommended Actions
                              </p>
                              <ul className="space-y-1">
                                {message.actions.map((a, i) => (
                                  <li key={i} className="text-xs text-text-body">
                                    {i + 1}. {a}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </Card>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-canvas-subtle rounded-2xl rounded-bl-sm px-6 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-brand rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-brand rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-brand rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={chatEndRef} />
          </div>
        )}

        {/* Empty State */}
        {chatHistory.length === 0 && (
          <Card>
            <div className="text-center py-12">
              <Icons.sparkles className="mx-auto text-brand mb-4" size={48} />
              <h3 className="text-lg font-bold text-ink mb-2">Start a Conversation</h3>
              <p className="text-sm text-text-muted mb-6">
                Ask questions about payroll readiness, risks, forecasts, and more
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {quickQuestions.map((q) => (
                  <Button
                    key={q}
                    variant="secondary"
                    size="sm"
                    onClick={() => askQuestion(q)}
                    disabled={isLoading}
                  >
                    {q}
                  </Button>
                ))}
              </div>
            </div>
          </Card>
        )}

        {/* Input Area */}
        <Card>
          <div className="flex gap-3">
            <Input
              placeholder="Ask about payroll readiness, risks, forecasts..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1"
              disabled={isLoading}
            />
            <Button 
              variant="primary" 
              onClick={() => askQuestion(question)}
              disabled={!question.trim() || isLoading}
            >
              <Icons.send size={16} />
            </Button>
          </div>
          <p className="text-xs text-text-muted mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </Card>
      </div>
    </Layout>
  );
}
