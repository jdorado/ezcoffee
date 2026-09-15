import { useEffect, useRef } from 'react'
import type { FC, KeyboardEvent as ReactKeyboardEvent, PointerEvent as ReactPointerEvent } from 'react'


type ChatComposerProps = {
  value: string
  disabled?: boolean
  busy?: boolean
  onChange: (value: string) => void
  onSend: () => void
}

const ChatComposer: FC<ChatComposerProps> = ({
  value,
  disabled = false,
  busy = false,
  onChange,
  onSend,
}) => {

  const sentOnTouchRef = useRef(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
  }, [value])
  const canSend = !disabled && !busy && value.trim().length > 0

  const handleKeyDown = (event: ReactKeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      if (disabled || busy) return
      onSend()
    }
  }

  const handleSendClick = () => {
    // iOS delivers the compatibility click after the touch press. The message was
    // already sent in handleSendPointerDown, while the keyboard was still stable.
    if (sentOnTouchRef.current) {
      sentOnTouchRef.current = false
      return
    }
    if (!canSend) return
    onSend()
  }

  const handleSendPointerDown = (event: ReactPointerEvent<HTMLButtonElement>) => {
    if (event.pointerType === 'mouse' || !canSend) return

    // On iPhone, tapping a button beside a focused textarea can blur the field
    // before click and move the fixed composer underneath the finger. Send on
    // the touch press and preserve focus so the button remains tappable.
    event.preventDefault()
    sentOnTouchRef.current = true
    onSend()
  }

  return (
    <div className="chat-input">
      <textarea
        ref={textareaRef}
        aria-label="Message"
        placeholder={disabled ? 'Working…' : 'Ask about a coffee or log a shot…'}
        value={value}
        disabled={disabled}
        rows={1}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        autoCorrect="off"
        autoCapitalize="off"
        autoComplete="off"
        spellCheck={false}
      />
      <button
        className="primary"
        type="button"
        onPointerDown={handleSendPointerDown}
        onClick={handleSendClick}
        disabled={!canSend}
        aria-label={'Send'}
        title={'Send'}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M5 12h14" />
          <path d="m13 6 6 6-6 6" />
        </svg>
      </button>
    </div>
  )
}

export default ChatComposer
