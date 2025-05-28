'use client'

import React, { useState, useEffect } from 'react'

const PhotoCarousel = () => {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isAutoPlay, setIsAutoPlay] = useState(true)

  // Array de fotos - aquí pondrás las rutas reales
  const photos = [
    {
      src: '/static/images/about/foto-1.jpg',
      alt: 'Análisis táctico en el ordenador'
    },
    {
      src: '/static/images/about/foto-2.jpg', 
      alt: 'Trabajando con visualizaciones de datos'
    },
    {
      src: '/static/images/about/foto-3.jpg',
      alt: 'En el estadio analizando el juego'
    },
    {
      src: '/static/images/about/foto-4.jpg',
      alt: 'Foto profesional Jaime Oriol'
    },
    {
      src: '/static/images/about/foto-5.jpg',
      alt: 'Contexto académico Universidad Francisco de Vitoria'
    }
  ]

  // Auto-play functionality
  useEffect(() => {
    if (!isAutoPlay) return
    
    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => 
        prevIndex === photos.length - 1 ? 0 : prevIndex + 1
      )
    }, 4000)

    return () => clearInterval(interval)
  }, [isAutoPlay, photos.length])

  const goToSlide = (index) => {
    setCurrentIndex(index)
  }

  const goToPrevious = () => {
    setCurrentIndex(currentIndex === 0 ? photos.length - 1 : currentIndex - 1)
  }

  const goToNext = () => {
    setCurrentIndex(currentIndex === photos.length - 1 ? 0 : currentIndex + 1)
  }

  const handleMouseEnter = () => setIsAutoPlay(false)
  const handleMouseLeave = () => setIsAutoPlay(true)

  return (
    <div className="relative w-full bg-gray-50 dark:bg-gray-900">
      {/* Contenedor principal del carrusel */}
      <div 
        className="relative h-96 md:h-[28rem] lg:h-[32rem] overflow-hidden"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {/* Imágenes */}
        <div 
          className="flex transition-transform duration-500 ease-in-out h-full"
          style={{ transform: `translateX(-${currentIndex * 100}%)` }}
        >
          {photos.map((photo, index) => (
            <div 
              key={index} 
              className="min-w-full h-full relative"
            >
              <img
                src={photo.src}
                alt={photo.alt}
                className="w-full h-full object-cover"
                loading={index === 0 ? "eager" : "lazy"}
              />
              {/* Overlay sutil para mejorar legibilidad si hay texto */}
              <div className="absolute inset-0 bg-black/10"></div>
            </div>
          ))}
        </div>

        {/* Controles de navegación */}
        <button
          onClick={goToPrevious}
          className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white/95 dark:bg-gray-800/80 dark:hover:bg-gray-800/95 p-2 rounded-full shadow-lg transition-all duration-200 z-10"
          aria-label="Imagen anterior"
        >
          <svg className="w-5 h-5 text-gray-800 dark:text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <button
          onClick={goToNext}
          className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white/95 dark:bg-gray-800/80 dark:hover:bg-gray-800/95 p-2 rounded-full shadow-lg transition-all duration-200 z-10"
          aria-label="Siguiente imagen"
        >
          <svg className="w-5 h-5 text-gray-800 dark:text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Indicadores (dots) */}
      <div className="flex justify-center space-x-2 py-4">
        {photos.map((_, index) => (
          <button
            key={index}
            onClick={() => goToSlide(index)}
            className={`w-3 h-3 rounded-full transition-all duration-200 ${
              index === currentIndex 
                ? 'bg-primary-500 scale-110' 
                : 'bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500'
            }`}
            aria-label={`Ir a la imagen ${index + 1}`}
          />
        ))}
      </div>
    </div>
  )
}

export default PhotoCarousel