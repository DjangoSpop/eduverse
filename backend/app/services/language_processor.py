"""
Multilingual curriculum processing with Arabic specialization

Supports language detection, OCR extraction, and cultural adaptation
for educational content in multiple languages.
"""
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Language detection will use langdetect when installed
try:
    import langdetect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not installed. Language detection will use fallback.")

# Tesseract OCR support (optional for MVP)
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not installed. OCR features disabled.")


class LanguageProcessor:
    """
    Detects and processes multilingual curriculum content
    with specialized handling for right-to-left languages
    """

    SUPPORTED_LANGUAGES = {
        'ar': {
            'name': 'Arabic',
            'native_name': 'العربية',
            'direction': 'rtl',
            'tesseract_lang': 'ara',
            'llm_model': 'claude-sonnet-4-20250514',  # Can use Mistral Saba for better Arabic
            'cultural_context': 'middle_eastern',
            'script': 'arabic'
        },
        'en': {
            'name': 'English',
            'native_name': 'English',
            'direction': 'ltr',
            'tesseract_lang': 'eng',
            'llm_model': 'claude-sonnet-4-20250514',
            'cultural_context': 'western',
            'script': 'latin'
        },
        'fr': {
            'name': 'French',
            'native_name': 'Français',
            'direction': 'ltr',
            'tesseract_lang': 'fra',
            'llm_model': 'claude-sonnet-4-20250514',
            'cultural_context': 'western',
            'script': 'latin'
        },
        'es': {
            'name': 'Spanish',
            'native_name': 'Español',
            'direction': 'ltr',
            'tesseract_lang': 'spa',
            'llm_model': 'claude-sonnet-4-20250514',
            'cultural_context': 'western',
            'script': 'latin'
        },
        'zh': {
            'name': 'Chinese',
            'native_name': '中文',
            'direction': 'ltr',
            'tesseract_lang': 'chi_sim',
            'llm_model': 'claude-sonnet-4-20250514',
            'cultural_context': 'eastern',
            'script': 'chinese'
        },
        'he': {
            'name': 'Hebrew',
            'native_name': 'עברית',
            'direction': 'rtl',
            'tesseract_lang': 'heb',
            'llm_model': 'claude-sonnet-4-20250514',
            'cultural_context': 'middle_eastern',
            'script': 'hebrew'
        },
        'ur': {
            'name': 'Urdu',
            'native_name': 'اردو',
            'direction': 'rtl',
            'tesseract_lang': 'urd',
            'llm_model': 'claude-sonnet-4-20250514',
            'cultural_context': 'south_asian',
            'script': 'arabic'
        }
    }

    @staticmethod
    def detect_language(text: str) -> Tuple[str, float]:
        """
        Detect language of curriculum text

        Args:
            text: Text to analyze

        Returns:
            (language_code, confidence_score)
        """
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short for reliable language detection")
            return 'en', 0.5

        if LANGDETECT_AVAILABLE:
            try:
                # Detect language with langdetect
                detected = langdetect.detect(text)

                # Get detailed probabilities for confidence
                probs = langdetect.detect_langs(text)
                confidence = next((p.prob for p in probs if p.lang == detected), 0.0)

                logger.info(f"Detected language: {detected} (confidence: {confidence:.2f})")
                return detected, confidence

            except Exception as e:
                logger.error(f"Language detection failed: {e}")
                return 'en', 0.5
        else:
            # Fallback: Simple heuristic detection
            return LanguageProcessor._fallback_detect_language(text)

    @staticmethod
    def _fallback_detect_language(text: str) -> Tuple[str, float]:
        """
        Simple fallback language detection using character ranges
        """
        # Count characters by script
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        latin_chars = sum(1 for c in text if 'a' <= c.lower() <= 'z')
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        hebrew_chars = sum(1 for c in text if '\u0590' <= c <= '\u05FF')

        total_chars = len(text)

        # Determine dominant script
        if arabic_chars / total_chars > 0.3:
            return 'ar', arabic_chars / total_chars
        elif hebrew_chars / total_chars > 0.3:
            return 'he', hebrew_chars / total_chars
        elif chinese_chars / total_chars > 0.3:
            return 'zh', chinese_chars / total_chars
        elif latin_chars / total_chars > 0.5:
            return 'en', latin_chars / total_chars
        else:
            return 'en', 0.4  # Default with low confidence

    @staticmethod
    def extract_text_with_ocr(
        image_data: bytes,
        language: str = 'ar',
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Extract text using OCR with language-specific optimization

        Critical for Arabic PDFs which may be image-based scans

        Args:
            image_data: Image bytes (from PDF page)
            language: Target language code
            config: Optional Tesseract configuration

        Returns:
            Dict with extracted text and metadata
        """
        if not TESSERACT_AVAILABLE:
            logger.error("Tesseract not available. Install pytesseract for OCR support.")
            return {
                'text': '',
                'language': language,
                'direction': LanguageProcessor.SUPPORTED_LANGUAGES.get(language, {}).get('direction', 'ltr'),
                'ocr_confidence': 0.0,
                'error': 'OCR not available'
            }

        if language not in LanguageProcessor.SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language for OCR: {language}, falling back to English")
            language = 'en'

        lang_config = LanguageProcessor.SUPPORTED_LANGUAGES[language]
        tesseract_lang = lang_config.get('tesseract_lang', 'eng')

        try:
            # Configure Tesseract for specific language
            custom_config = config or f'--oem 3 --psm 6 -l {tesseract_lang}'

            # Extract text with OCR
            text = pytesseract.image_to_string(
                image_data,
                config=custom_config
            )

            # Get confidence data
            try:
                data = pytesseract.image_to_data(
                    image_data,
                    config=custom_config,
                    output_type=pytesseract.Output.DICT
                )
                confidences = [int(c) for c in data['conf'] if c != '-1']
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except:
                avg_confidence = 0.0

            # Additional processing for RTL languages
            if lang_config['direction'] == 'rtl':
                text = LanguageProcessor._process_rtl_text(text, language)

            logger.info(f"OCR extracted {len(text)} characters with {avg_confidence:.1f}% confidence")

            return {
                'text': text,
                'language': language,
                'direction': lang_config['direction'],
                'ocr_confidence': avg_confidence / 100.0,  # Normalize to 0-1
                'script': lang_config.get('script', 'unknown')
            }

        except Exception as e:
            logger.error(f"OCR extraction failed for {language}: {e}")
            return {
                'text': '',
                'language': language,
                'direction': lang_config['direction'],
                'ocr_confidence': 0.0,
                'error': str(e)
            }

    @staticmethod
    def _process_rtl_text(text: str, language: str) -> str:
        """
        Post-process RTL text to ensure correct ordering
        Handles common OCR issues with Arabic and Hebrew text
        """
        # Remove extra whitespace common in RTL OCR
        text = ' '.join(text.split())

        if language == 'ar':
            # Normalize Arabic characters
            text = text.replace('ـ', '')  # Remove tatweel (elongation)
            text = text.replace('ى', 'ي')  # Normalize alif maksura
            # Optional: Normalize taa marbutah
            # text = text.replace('ة', 'ه')

            # Remove Arabic diacritics if desired (optional)
            # arabic_diacritics = re.compile(r'[\u064B-\u065F\u0670]')
            # text = arabic_diacritics.sub('', text)

        return text

    @staticmethod
    def get_cultural_prompts(language: str) -> Dict[str, str]:
        """
        Get culturally-appropriate prompt templates for content generation

        Critical for ensuring educational content is culturally sensitive
        and pedagogically appropriate for the target audience.

        Args:
            language: Language code (e.g., 'ar', 'en')

        Returns:
            Dict of cultural prompt templates
        """
        if language == 'ar':
            return {
                'learning_style': """
                    للطلاب العرب، استخدم:
                    - أمثلة من البيئة المحلية والثقافة العربية (الصحراء، التمور، الجمال)
                    - قصص تحتوي على قيم عربية وإسلامية (التعاون، الصدق، الاحترام)
                    - شخصيات بأسماء عربية مألوفة (محمد، فاطمة، علي، نورة)
                    - ألعاب تراعي الحساسية الثقافية والدينية
                """,
                'gamification': """
                    ميكانيكا الألعاب المناسبة ثقافياً:
                    - التعاون والعمل الجماعي أكثر من المنافسة الفردية
                    - مكافآت تحترم القيم الثقافية (نجوم، شهادات، أوسمة)
                    - قصص تعليمية مبنية على الأمثال والحكم العربية
                    - تجنب القمار والمراهنة في آليات اللعب
                """,
                'mentor_personality': """
                    شخصية المرشد الذكي باللغة العربية:
                    - استخدام لغة محترمة ومهذبة (خطاب بالمثنى أو الجمع)
                    - صبور ومشجع مع تجنب النقد القاسي
                    - استخدام تعابير عربية مألوفة:
                      * "ما شاء الله" عند النجاح
                      * "أحسنت" للتشجيع
                      * "بارك الله فيك" للمكافأة
                      * "حاول مرة أخرى" عند الخطأ
                    - احترام أوقات الصلاة وعدم المقاطعة
                """,
                'content_safety': """
                    إرشادات السلامة الثقافية:
                    - تجنب المحتوى المحرم (الخمر، الخنزير، القمار)
                    - عدم تصوير المحتوى غير المحتشم
                    - احترام الرموز الدينية
                    - تجنب المواضيع الحساسة سياسياً
                    - استخدام أمثلة من البيئة العربية الإسلامية
                """,
                'examples': """
                    أمثلة مناسبة للسياق العربي:
                    - الحيوانات: جمل، حصان، أغنام، نحل (تجنب: خنزير، كلب)
                    - الأطعمة: تمر، زيتون، خبز، لبن (تجنب: لحم خنزير)
                    - الأماكن: مسجد، سوق، واحة، صحراء
                    - المناسبات: عيد الفطر، عيد الأضحى، رمضان
                """
            }

        elif language == 'en':
            return {
                'learning_style': """
                    For English-speaking students:
                    - Use diverse, inclusive examples from various cultures
                    - Encourage curiosity, questioning, and critical thinking
                    - Celebrate individual achievement and effort
                    - Interactive, discovery-based learning approaches
                    - Growth mindset messaging (mistakes are learning opportunities)
                """,
                'gamification': """
                    Effective game mechanics for English learners:
                    - Balance competition and collaboration
                    - Immediate positive feedback and rewards
                    - Progressive challenge and mastery paths
                    - Achievement badges and leaderboards
                    - XP and leveling systems
                """,
                'mentor_personality': """
                    AI mentor personality for English:
                    - Friendly, encouraging, and enthusiastic
                    - Uses casual, age-appropriate language
                    - Celebrates mistakes as learning opportunities
                    - Phrases:
                      * "Great job!" for success
                      * "Nice try! Let's learn from this" for errors
                      * "You're on fire!" for streaks
                      * "Keep going, you've got this!" for encouragement
                """,
                'content_safety': """
                    Content safety guidelines:
                    - Inclusive representation (diverse characters, backgrounds)
                    - Age-appropriate content (no violence, inappropriate themes)
                    - Avoid stereotypes
                    - Respectful of all cultures and religions
                    - Gender-neutral language where appropriate
                """,
                'examples': """
                    Appropriate examples for English context:
                    - Animals: dogs, cats, elephants, penguins
                    - Foods: pizza, sandwiches, fruits, vegetables
                    - Places: parks, libraries, museums, beaches
                    - Celebrations: birthdays, holidays (diverse)
                """
            }

        elif language == 'zh':
            return {
                'learning_style': """
                    For Chinese-speaking students:
                    - Emphasis on diligence, respect, and academic excellence
                    - Group learning and peer collaboration
                    - Reference to Chinese cultural values and history
                    - Use of familiar Chinese examples and contexts
                """,
                'mentor_personality': """
                    AI mentor for Chinese learners:
                    - Respectful and patient
                    - Emphasizes hard work and persistence
                    - Phrases:
                      * "很好!" (Very good!)
                      * "继续努力!" (Keep working hard!)
                      * "你做得很棒!" (You did great!)
                """
            }

        else:
            # Generic/default cultural prompts
            return {
                'learning_style': "Use age-appropriate, engaging examples relevant to the student's culture",
                'gamification': "Balance challenge and fun with appropriate rewards",
                'mentor_personality': "Friendly, encouraging, and supportive",
                'content_safety': "Ensure all content is age-appropriate and culturally respectful"
            }

    @staticmethod
    def validate_content_safety(text: str, language: str) -> Tuple[bool, List[str]]:
        """
        Validate generated content for cultural appropriateness and safety

        Args:
            text: Content to validate
            language: Language code

        Returns:
            (is_safe, list_of_issues)
        """
        issues = []

        if language == 'ar':
            # Check for culturally sensitive topics (Arabic/Islamic context)
            sensitive_keywords = {
                'خمر': 'alcohol reference',
                'خنزير': 'pork reference',
                'قمار': 'gambling reference',
                'كحول': 'alcohol reference',
                'ميسر': 'gambling reference'
            }

            for keyword, issue_type in sensitive_keywords.items():
                if keyword in text:
                    issues.append(f"Contains culturally sensitive content: {issue_type}")

            # Verify appropriate greetings and phrases are used
            appropriate_phrases = ['السلام عليكم', 'بارك الله فيك', 'ما شاء الله', 'أحسنت']

            # For longer text, expect some cultural appropriateness
            if len(text) > 200:
                has_appropriate_content = any(phrase in text for phrase in appropriate_phrases)
                if not has_appropriate_content:
                    # Not critical, but note it
                    logger.info("Arabic content could benefit from more culturally appropriate phrases")

        elif language == 'en':
            # Check for inappropriate content (English context)
            inappropriate_terms = ['violence', 'weapon', 'drugs', 'alcohol']
            for term in inappropriate_terms:
                if term.lower() in text.lower():
                    issues.append(f"May contain inappropriate content: {term}")

        is_safe = len(issues) == 0

        if not is_safe:
            logger.warning(f"Content safety issues detected: {issues}")

        return is_safe, issues

    @staticmethod
    def get_language_config(language_code: str) -> Optional[Dict]:
        """
        Get configuration for a specific language

        Args:
            language_code: Language code (e.g., 'ar', 'en')

        Returns:
            Language configuration dict or None if not supported
        """
        return LanguageProcessor.SUPPORTED_LANGUAGES.get(language_code)

    @staticmethod
    def is_rtl_language(language_code: str) -> bool:
        """Check if language is right-to-left"""
        lang_config = LanguageProcessor.get_language_config(language_code)
        return lang_config.get('direction') == 'rtl' if lang_config else False

    @staticmethod
    def list_supported_languages() -> List[Dict]:
        """
        Get list of all supported languages

        Returns:
            List of language info dicts
        """
        languages = []
        for code, config in LanguageProcessor.SUPPORTED_LANGUAGES.items():
            languages.append({
                'code': code,
                'name': config['name'],
                'native_name': config.get('native_name', config['name']),
                'direction': config['direction'],
                'script': config.get('script', 'unknown')
            })
        return languages
