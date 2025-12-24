"""
Streamlit Web Interface for Real-Time Multilingual Query Handler
"""

import streamlit as st
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Real-Time Multilingual Query Handler",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.25rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 0.25rem;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🌐 Real-Time Multilingual Query Handler</h1>', unsafe_allow_html=True)
st.markdown("---")

# Initialize session state
if "translation_history" not in st.session_state:
    st.session_state.translation_history = []

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Status
    st.subheader("Service Status")
    api_key = os.getenv("GROQ_API_KEY")
    
    if api_key:
        st.success("🟢 API Key: Configured")
        st.info(f"Key: {api_key[:10]}...")
    else:
        st.error("🔴 API Key: Missing")
    
    st.markdown("---")
    
    # Language Settings
    st.subheader("Language Settings")
    
    source_lang_options = {
        "auto": "🔍 Auto Detect",
        "en": "🇺🇸 English",
        "es": "🇪🇸 Spanish",
        "fr": "🇫🇷 French",
        "de": "🇩🇪 German",
        "it": "🇮🇹 Italian",
        "pt": "🇵🇹 Portuguese",
        "ru": "🇷🇺 Russian",
        "ja": "🇯🇵 Japanese",
        "ko": "🇰🇷 Korean",
        "zh": "🇨🇳 Chinese",
        "ar": "🇸🇦 Arabic",
        "hi": "🇮🇳 Hindi"
    }
    
    selected_source = st.selectbox(
        "Source Language:",
        options=list(source_lang_options.keys()),
        format_func=lambda x: source_lang_options[x],
        index=0
    )
    
    # Target language options
    target_lang_options = {
        "English": "🇺🇸 English",
        "Spanish": "🇪🇸 Spanish", 
        "French": "🇫🇷 French",
        "German": "🇩🇪 German",
        "Italian": "🇮🇹 Italian",
        "Portuguese": "🇵🇹 Portuguese",
        "Russian": "🇷🇺 Russian",
        "Japanese": "🇯🇵 Japanese",
        "Korean": "🇰🇷 Korean",
        "Chinese": "🇨🇳 Chinese",
        "Arabic": "🇸🇦 Arabic",
        "Hindi": "🇮🇳 Hindi"
    }
    
    selected_target = st.selectbox(
        "Target Language:",
        options=list(target_lang_options.keys()),
        format_func=lambda x: target_lang_options[x],
        index=0  # Default to English
    )
    
    st.markdown("---")
    
    # Statistics
    st.subheader("📊 Session Statistics")
    st.metric("Total Translations", len(st.session_state.translation_history))
    
    if st.session_state.translation_history:
        successful = sum(1 for h in st.session_state.translation_history if h.get("success", False))
        success_rate = (successful / len(st.session_state.translation_history)) * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Input Query")
    
    # Text input
    query_text = st.text_area(
        "Enter your query in any language:",
        height=150,
        placeholder="Type or paste your message here...",
        key="query_input"
    )
    
    # Character count
    char_count = len(query_text)
    st.caption(f"Characters: {char_count}/1000")
    
    # Language detection preview
    if query_text.strip() and selected_source == "auto":
        if len(query_text.strip()) >= 10:  # Reduced minimum for better UX
            try:
                from langdetect import detect, detect_langs
                
                # Get multiple possibilities
                detections = detect_langs(query_text)
                if detections:
                    best = max(detections, key=lambda x: x.prob)
                    
                    # Improved confidence handling
                    if best.prob >= 0.8:
                        confidence_level = "High"
                        confidence_color = "🟢"
                    elif best.prob >= 0.6:
                        confidence_level = "Good"
                        confidence_color = "🟡"
                    elif best.prob >= 0.4:
                        confidence_level = "Fair"
                        confidence_color = "🟠"
                    else:
                        confidence_level = "Low"
                        confidence_color = "🔴"
                    
                    # Handle common misdetections with better logic
                    if best.lang in ['cy', 'ga', 'mt', 'is', 'eu'] and best.prob < 0.85:
                        # Check for English indicators
                        english_indicators = [
                            'the', 'and', 'or', 'is', 'are', 'was', 'were', 'have', 'has', 'had',
                            'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must',
                            'this', 'that', 'these', 'those', 'with', 'from', 'they', 'them',
                            'what', 'when', 'where', 'why', 'how', 'who', 'which'
                        ]
                        text_lower = query_text.lower()
                        english_count = sum(1 for word in english_indicators if f' {word} ' in f' {text_lower} ' or text_lower.startswith(f'{word} ') or text_lower.endswith(f' {word}'))
                        
                        if english_count >= 1:  # If contains English indicators
                            st.info(f"🔍 Detected Language: 🇺🇸 English (auto-corrected from {best.lang})")
                        else:
                            lang_name = source_lang_options.get(best.lang, best.lang.upper())
                            st.info(f"🔍 Detected Language: {lang_name} {confidence_color} ({confidence_level}: {best.prob:.2f})")
                    else:
                        lang_name = source_lang_options.get(best.lang, best.lang.upper())
                        st.info(f"🔍 Detected Language: {lang_name} {confidence_color} ({confidence_level}: {best.prob:.2f})")
                    
                    # Show alternative possibilities if confidence is low
                    if best.prob < 0.6 and len(detections) > 1:
                        alternatives = [f"{source_lang_options.get(d.lang, d.lang.upper())} ({d.prob:.2f})" 
                                      for d in sorted(detections, key=lambda x: x.prob, reverse=True)[:3]]
                        st.caption(f"💡 Other possibilities: {', '.join(alternatives)}")
                        
            except Exception as e:
                st.warning("⚠️ Could not detect language reliably - will use auto-detection during translation")
        else:
            st.info("💡 Enter at least 10 characters for language detection")
    
    # Translate button
    translate_button = st.button(
        f"🚀 Translate to {selected_target}",
        type="primary",
        disabled=not query_text.strip() or not api_key,
        use_container_width=True
    )

with col2:
    st.header("🌍 Translation Result")
    
    if translate_button and query_text.strip():
        with st.spinner("Translating..."):
            start_time = time.time()
            
            try:
                # Import services only when needed
                from translation_service import TranslationService
                
                # Initialize translation service
                translator = TranslationService()
                
                # Perform translation
                result = translator.translate_text(query_text, selected_source, selected_target)
                
                processing_time = time.time() - start_time
                
                # Add to history
                history_entry = {
                    "original": query_text,
                    "translation": result.get("translation", ""),
                    "source_lang": result.get("source_lang", selected_source),
                    "success": result.get("success", False),
                    "processing_time": processing_time,
                    "timestamp": time.strftime("%H:%M:%S")
                }
                st.session_state.translation_history.append(history_entry)
                
                # Display results
                if result["success"]:
                    st.markdown(f"""
                    <div class="success-message">
                        <h4>✅ Translation Successful</h4>
                        <p><strong>Source:</strong> {result["source_lang"]} → <strong>Target:</strong> {selected_target}</p>
                        <p><strong>Processing Time:</strong> {processing_time:.2f} seconds</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Translation output
                    st.subheader(f"📋 Translated Text ({selected_target})")
                    st.text_area(
                        f"{selected_target} Translation:",
                        value=result["translation"],
                        height=100,
                        disabled=True,
                        key="translation_output"
                    )
                    
                    # Additional info
                    with st.expander("📊 Translation Details"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Model Used", result.get("model_used", "Llama 3.1"))
                        with col_b:
                            st.metric("Characters", f"{len(query_text)} → {len(result['translation'])}")
                
                else:
                    st.markdown(f"""
                    <div class="error-message">
                        <h4>❌ Translation Failed</h4>
                        <p><strong>Error:</strong> {result.get("error", "Unknown error")}</p>
                        <p><strong>Processing Time:</strong> {processing_time:.2f} seconds</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.translation_history.append({
                    "original": query_text,
                    "translation": "",
                    "success": False,
                    "error": str(e),
                    "timestamp": time.strftime("%H:%M:%S")
                })

# Translation History
if st.session_state.translation_history:
    st.markdown("---")
    st.subheader("📚 Translation History")
    
    # Show last 5 translations
    recent_history = st.session_state.translation_history[-5:]
    
    for i, entry in enumerate(reversed(recent_history)):
        with st.expander(f"{entry['timestamp']} - {entry['original'][:50]}..."):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**Original:**")
                st.write(entry['original'])
            with col_b:
                st.write("**Translation:**")
                if entry['success']:
                    st.write(entry['translation'])
                    st.success(f"✅ Success ({entry.get('processing_time', 0):.2f}s)")
                else:
                    st.error(f"❌ Failed: {entry.get('error', 'Unknown error')}")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Features:**")
    st.markdown("• Real-time translation")
    st.markdown("• 50+ languages supported")
    st.markdown("• Customer support optimized")

with col2:
    st.markdown("**Powered By:**")
    st.markdown("• Groq API")
    st.markdown("• Llama 3.1 Model")
    st.markdown("• Streamlit")

with col3:
    st.markdown("**Status:**")
    if api_key:
        st.markdown("🟢 Ready to translate")
    else:
        st.markdown("🔴 API key required")

# Clear history button
if st.session_state.translation_history:
    if st.button("🗑️ Clear History"):
        st.session_state.translation_history = []
        st.rerun()