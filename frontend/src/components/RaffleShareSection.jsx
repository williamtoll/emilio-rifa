import { useState } from 'react'
import SocialShareButtons from './SocialShareButtons'
import { copyToClipboard } from '../utils/clipboard'
import { buildRaffleBuyShareText, getRaffleBuyUrl } from '../utils/socialShare'
import './RaffleShareSection.css'

export default function RaffleShareSection({
  raffleId,
  raffleName,
  priceLabel,
  availableLabel,
  imageUrl,
  onNotice,
  onError,
  compact = false,
  className = '',
}) {
  const [localNotice, setLocalNotice] = useState(null)
  const buyUrl = getRaffleBuyUrl(raffleId)
  const shareText = buildRaffleBuyShareText(raffleName, buyUrl, { priceLabel, availableLabel })

  const notify = (msg) => {
    setLocalNotice(msg)
    onNotice?.(msg)
  }

  const handleCopy = async () => {
    try {
      await copyToClipboard(buyUrl)
      notify('Enlace copiado')
    } catch {
      onError?.('No se pudo copiar el enlace')
    }
  }

  return (
    <section className={`raffle-share-section ${compact ? 'raffle-share-section--compact' : ''} ${className}`}>
      {!compact && (
        <>
          <h3 className="raffle-share-title">Compartir sorteo</h3>
          <p className="raffle-share-desc">
            Compartí este enlace en Facebook o Instagram para que otros ingresen y elijan su número de ticket.
          </p>
        </>
      )}

      <div className="raffle-share-url-row">
        <a href={buyUrl} target="_blank" rel="noopener noreferrer" className="raffle-share-url">
          {buyUrl}
        </a>
        <button type="button" className="btn btn-secondary btn-sm" onClick={handleCopy}>
          Copiar
        </button>
      </div>

      {localNotice && (
        <p className="raffle-share-notice">{localNotice}</p>
      )}

      <SocialShareButtons
        url={buyUrl}
        text={shareText}
        imageUrl={imageUrl}
        imageFilename={`sorteo-${raffleId}.jpg`}
        onNotice={notify}
        onError={onError}
        className="raffle-share-social"
      />
    </section>
  )
}
