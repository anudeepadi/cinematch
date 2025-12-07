import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings2, Sparkles, X, MessageSquare, Layers, Send, Bot, ChevronDown } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { MoodSelector, WatchingWithSelector, RecommendationStack } from '../components/recommendations';
import { Button } from '../components/common/Button';
import { useRecommendationStore } from '../store/recommendationStore';
import { moviesApi } from '../api/movies';
import { companionsApi } from '../api/companions';
import { chatApi } from '../api/chat';
import { Genre, Companion, ChatMessage } from '../types';

type TabType = 'recommendations' | 'chat';
type AIModel = 'claude' | 'openai' | 'gemini';

const AI_MODELS: { id: AIModel; name: string; icon: string; color: string }[] = [
  { id: 'claude', name: 'Claude', icon: '🎭', color: 'from-orange-500 to-amber-500' },
  { id: 'openai', name: 'GPT-4', icon: '🤖', color: 'from-green-500 to-emerald-500' },
  { id: 'gemini', name: 'Gemini', icon: '✨', color: 'from-blue-500 to-indigo-500' },
];

export function RecommendationsPage() {
  const [showFilterOverlay, setShowFilterOverlay] = useState(false);
  const [genres, setGenres] = useState<Genre[]>([]);
  const [companions, setCompanions] = useState<Companion[]>([]);
  const [hasGenerated, setHasGenerated] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('recommendations');

  // Chat state
  const [selectedModel, setSelectedModel] = useState<AIModel>('claude');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const {
    recommendations,
    isLoading,
    mood,
    watchingWith,
    selectedCompanion,
    manualCompanionPrefs,
    setMood,
    setWatchingWith,
    setCompanion,
    setManualCompanionPrefs,
    generateRecommendations,
    resetRecommendations,
  } = useRecommendationStore();

  useEffect(() => {
    // Load genres and companions
    moviesApi.getGenres().then(setGenres).catch(console.error);
    companionsApi.getCompanions().then(comps => {
      setCompanions(comps.filter(c => c.status === 'accepted'));
    }).catch(console.error);
  }, []);

  // Scroll chat to bottom on new messages
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const handleGenerate = async () => {
    await generateRecommendations();
    setHasGenerated(true);
    setShowFilterOverlay(false);
  };

  const handleRefresh = async () => {
    const excludeIds = recommendations.map(r => r.movie_id);
    await generateRecommendations(excludeIds);
  };

  const handleComplete = () => {
    // All cards swiped - show filter overlay
    setShowFilterOverlay(true);
  };

  const handleReset = () => {
    resetRecommendations();
    setHasGenerated(false);
    setShowFilterOverlay(true);
  };

  const handleSendChat = async () => {
    if (!chatInput.trim() || isChatLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      const response = await chatApi.sendMessage({
        message: chatInput.trim(),
        model: selectedModel,
        context: {
          mood,
          watchingWith,
          recentRecommendations: recommendations.slice(0, 5).map(r => ({
            title: r.title,
            movie_id: r.movie_id,
          })),
        },
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        model: selectedModel,
        movieSuggestions: response.movie_suggestions,
      };

      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        model: selectedModel,
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const selectedModelInfo = AI_MODELS.find(m => m.id === selectedModel)!;

  return (
    <Layout>
      <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <motion.h1
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-3xl sm:text-4xl font-bold text-white mb-2"
            >
              <span className="bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
                For You
              </span>
            </motion.h1>
            <p className="text-zinc-400">
              AI-powered recommendations tailored to your taste
            </p>
          </div>

          {/* Tab Switcher */}
          <div className="flex justify-center mb-6">
            <div className="inline-flex bg-zinc-900/50 border border-zinc-800 rounded-xl p-1">
              <button
                onClick={() => setActiveTab('recommendations')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'recommendations'
                    ? 'bg-amber-500 text-white'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                <Layers size={18} />
                Swipe
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'chat'
                    ? 'bg-amber-500 text-white'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                <MessageSquare size={18} />
                Chat
              </button>
            </div>
          </div>

          {/* Preferences Button (for Swipe tab) */}
          {activeTab === 'recommendations' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8"
            >
              <button
                onClick={() => setShowFilterOverlay(true)}
                className="w-full flex items-center justify-between p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-zinc-700 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Settings2 size={20} className="text-zinc-400" />
                  <span className="font-medium text-white">Preferences</span>
                  {(mood || watchingWith) && (
                    <div className="flex items-center gap-2">
                      {mood && (
                        <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 text-xs rounded-full">
                          {mood}
                        </span>
                      )}
                      {watchingWith && (
                        <span className="px-2 py-0.5 bg-zinc-700 text-zinc-300 text-xs rounded-full">
                          {watchingWith}
                        </span>
                      )}
                    </div>
                  )}
                </div>
                <Sparkles size={20} className="text-amber-500" />
              </button>
            </motion.div>
          )}

          {/* Content Area */}
          <AnimatePresence mode="wait">
            {activeTab === 'recommendations' ? (
              <motion.div
                key="recommendations"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="relative"
              >
                {/* Show prompt to select filters if no recommendations yet */}
                {!hasGenerated && recommendations.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-[500px] text-center">
                    <motion.div
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="w-24 h-24 rounded-full bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center mb-6"
                    >
                      <Sparkles size={40} className="text-amber-500" />
                    </motion.div>
                    <h3 className="text-xl font-semibold text-white mb-2">
                      Ready to discover?
                    </h3>
                    <p className="text-zinc-400 mb-6 max-w-sm">
                      Set your mood and preferences to get personalized movie recommendations
                    </p>
                    <Button
                      onClick={() => setShowFilterOverlay(true)}
                      icon={<Settings2 size={18} />}
                      size="lg"
                    >
                      Select Filters
                    </Button>
                  </div>
                ) : (
                  <RecommendationStack
                    recommendations={recommendations}
                    isLoading={isLoading}
                    onRefresh={handleRefresh}
                    onComplete={handleComplete}
                  />
                )}
              </motion.div>
            ) : (
              <motion.div
                key="chat"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="relative"
              >
                {/* Chat Interface */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl overflow-hidden">
                  {/* Model Selector */}
                  <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
                    <div className="relative">
                      <button
                        onClick={() => setShowModelDropdown(!showModelDropdown)}
                        className="flex items-center gap-2 px-3 py-2 bg-zinc-800 rounded-lg hover:bg-zinc-700 transition-colors"
                      >
                        <span className="text-lg">{selectedModelInfo.icon}</span>
                        <span className="text-sm font-medium text-white">{selectedModelInfo.name}</span>
                        <ChevronDown size={16} className={`text-zinc-400 transition-transform ${showModelDropdown ? 'rotate-180' : ''}`} />
                      </button>

                      <AnimatePresence>
                        {showModelDropdown && (
                          <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="absolute top-full left-0 mt-2 bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden z-10 min-w-[160px]"
                          >
                            {AI_MODELS.map((model) => (
                              <button
                                key={model.id}
                                onClick={() => {
                                  setSelectedModel(model.id);
                                  setShowModelDropdown(false);
                                }}
                                className={`w-full flex items-center gap-2 px-3 py-2 hover:bg-zinc-700 transition-colors ${
                                  selectedModel === model.id ? 'bg-zinc-700' : ''
                                }`}
                              >
                                <span className="text-lg">{model.icon}</span>
                                <span className="text-sm text-white">{model.name}</span>
                              </button>
                            ))}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>

                    <p className="text-xs text-zinc-500">
                      Ask for movie recommendations
                    </p>
                  </div>

                  {/* Chat Messages */}
                  <div
                    ref={chatContainerRef}
                    className="h-[400px] overflow-y-auto p-4 space-y-4"
                  >
                    {chatMessages.length === 0 ? (
                      <div className="flex flex-col items-center justify-center h-full text-center">
                        <Bot size={48} className="text-zinc-600 mb-4" />
                        <h3 className="text-lg font-medium text-zinc-300 mb-2">
                          Chat with AI
                        </h3>
                        <p className="text-sm text-zinc-500 max-w-sm">
                          Ask for movie recommendations, describe what you're in the mood for, or get personalized suggestions based on your taste.
                        </p>
                        <div className="mt-4 flex flex-wrap justify-center gap-2">
                          {[
                            "Suggest a thriller like Inception",
                            "What's a good family movie?",
                            "I want something mind-bending",
                          ].map((suggestion) => (
                            <button
                              key={suggestion}
                              onClick={() => setChatInput(suggestion)}
                              className="px-3 py-1.5 bg-zinc-800 text-zinc-300 text-xs rounded-full hover:bg-zinc-700 transition-colors"
                            >
                              {suggestion}
                            </button>
                          ))}
                        </div>
                      </div>
                    ) : (
                      chatMessages.map((message) => (
                        <motion.div
                          key={message.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                              message.role === 'user'
                                ? 'bg-amber-500 text-white'
                                : 'bg-zinc-800 text-zinc-100'
                            }`}
                          >
                            {message.role === 'assistant' && message.model && (
                              <div className="flex items-center gap-1 text-xs text-zinc-400 mb-1">
                                <span>{AI_MODELS.find(m => m.id === message.model)?.icon}</span>
                                <span>{AI_MODELS.find(m => m.id === message.model)?.name}</span>
                              </div>
                            )}
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>

                            {/* Movie Suggestions */}
                            {message.movieSuggestions && message.movieSuggestions.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-zinc-700 space-y-2">
                                {message.movieSuggestions.map((movie, idx) => (
                                  <div
                                    key={idx}
                                    className="flex items-center gap-3 p-2 bg-zinc-900/50 rounded-lg"
                                  >
                                    {movie.poster_url && (
                                      <img
                                        src={movie.poster_url}
                                        alt={movie.title}
                                        className="w-10 h-14 object-cover rounded"
                                      />
                                    )}
                                    <div className="flex-1 min-w-0">
                                      <p className="text-sm font-medium text-white truncate">
                                        {movie.title}
                                      </p>
                                      {movie.year && (
                                        <p className="text-xs text-zinc-400">{movie.year}</p>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </motion.div>
                      ))
                    )}

                    {isChatLoading && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex justify-start"
                      >
                        <div className="bg-zinc-800 rounded-2xl px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex gap-1">
                              <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                              <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                              <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </div>

                  {/* Chat Input */}
                  <div className="p-4 border-t border-zinc-800">
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        handleSendChat();
                      }}
                      className="flex gap-2"
                    >
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        placeholder="Ask for movie recommendations..."
                        className="flex-1 px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-amber-500 transition-colors"
                        disabled={isChatLoading}
                      />
                      <Button
                        type="submit"
                        disabled={!chatInput.trim() || isChatLoading}
                        icon={<Send size={18} />}
                      >
                        Send
                      </Button>
                    </form>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Reset button */}
          {activeTab === 'recommendations' && hasGenerated && !isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-24 text-center"
            >
              <button
                onClick={handleReset}
                className="text-sm text-zinc-500 hover:text-zinc-400 transition-colors"
              >
                Start over with new preferences
              </button>
            </motion.div>
          )}
        </div>
      </div>

      {/* Filter Overlay */}
      <AnimatePresence>
        {showFilterOverlay && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-end sm:items-center justify-center"
          >
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowFilterOverlay(false)}
              className="absolute inset-0 bg-black/80 backdrop-blur-sm"
            />

            {/* Overlay Content */}
            <motion.div
              initial={{ opacity: 0, y: 100 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 100 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-zinc-900 border border-zinc-800 rounded-t-3xl sm:rounded-2xl shadow-2xl"
            >
              {/* Header */}
              <div className="sticky top-0 z-10 flex items-center justify-between p-4 bg-zinc-900/95 backdrop-blur border-b border-zinc-800">
                <h2 className="text-lg font-semibold text-white">Select Preferences</h2>
                <button
                  onClick={() => setShowFilterOverlay(false)}
                  className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Content */}
              <div className="p-6 space-y-8">
                {/* Mood Selector */}
                <MoodSelector
                  selectedMood={mood}
                  onSelect={setMood}
                />

                {/* Watching With Selector */}
                <WatchingWithSelector
                  selectedContext={watchingWith}
                  onSelectContext={setWatchingWith}
                  companions={companions}
                  selectedCompanion={selectedCompanion}
                  onSelectCompanion={setCompanion}
                  manualPreferences={manualCompanionPrefs}
                  onSetManualPreferences={setManualCompanionPrefs}
                  genres={genres}
                />
              </div>

              {/* Footer */}
              <div className="sticky bottom-0 p-4 bg-zinc-900/95 backdrop-blur border-t border-zinc-800 flex gap-3">
                <Button
                  variant="secondary"
                  onClick={() => setShowFilterOverlay(false)}
                  className="flex-1"
                >
                  Back
                </Button>
                <Button
                  onClick={handleGenerate}
                  isLoading={isLoading}
                  icon={<Sparkles size={18} />}
                  className="flex-1"
                >
                  {hasGenerated ? 'Update' : 'Get Recommendations'}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </Layout>
  );
}
