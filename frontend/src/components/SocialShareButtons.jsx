import { useState } from 'react'
import { openFacebookShare, shareToInstagram } from '../utils/socialShare'
import './SocialShareButtons.css'

export default function SocialShareButtons({
  url,
  text,
  imageUrl,
  imageFilename,
  onNotice,
  onError,
  size = 'sm',
  className = '',
}) {
  const [igLoading, setIgLoading] = useState(false)
  const sizeClass = size === 'sm' ? 'btn-sm' : ''

  const handleFacebook = () => {
    if (!url) {
      onError?.('No hay enlace para compartir')
      return
    }
    openFacebookShare(url)
  }

  const handleInstagram = async () => {
    setIgLoading(true)
    try {
      const mode = await shareToInstagram({ url, text, imageUrl, imageFilename })
      if (mode === 'image') {
        onNotice?.('Imagen descargada y texto copiado. Abrí Instagram para publicar.')
      } else {
        onNotice?.('Texto copiado. Pegalo en Instagram (historia, bio o mensaje).')
      }
    } catch (err) {
      onError?.(err.message || 'No se pudo preparar para Instagram')
    } finally {
      setIgLoading(false)
    }
  }

  return (
    <div className={`social-share-buttons ${className}`}>
      <button
        type="button"
        className={`btn ${sizeClass} btn-facebook`}
        onClick={handleFacebook}
        disabled={!url}
        title="Compartir en Facebook"
      >
        Facebook
      </button>
      <button
        type="button"
        className={`btn ${sizeClass} btn-instagram`}
        onClick={handleInstagram}
        disabled={igLoading}
        title="Compartir en Instagram"
      >
        {igLoading ? '...' : 'Instagram'}
      </button>
    </div>
  )
}
