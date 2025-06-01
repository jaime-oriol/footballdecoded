'use client'

import React, { useState, useEffect } from 'react'
import Image from '@/components/Image'

const PhotoCarousel = () => {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isAutoPlay, setIsAutoPlay] = useState(true)

  // Array de fotos - aquí pondrás las rutas reales
  const photos = [
    {
      src: '/static/images/about/foto-1.jpg',
      alt: 'Análisis táctico en el ordenador',
    },
    {
      src: '/static/images/about/foto-2.jpg',
      alt: 'Trabajando con visualizaciones de datos',
    },
    {
      src: '/static/images/about/foto-3.jpg',
      alt: 'En el estadio analizando el juego',
    },
    {
      src: '/static/images/about/foto-4.jpg',
      alt: 'Foto profesional Jaime Oriol',
    },
    {
      src: '/static/images/about/foto-5.jpg',
      alt: 'Contexto académico Universidad Francisco de Vitoria',
    },
  ]

  // Auto-play functionality
  useEffect(() => {
    if (!isAutoPlay) return

    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex === photos.length - 1 ? 0 : prevIndex + 1))
    }, 4000)

    return () => clearInterval(interval)
  }, [isAutoPlay, photos.length])

  const goToSlide = (index: number) => {
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
        className="relative h-96 overflow-hidden md:h-[28rem] lg:h-[32rem]"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {/* Imágenes */}
        <div
          className="flex h-full transition-transform duration-500 ease-in-out"
          style={{ transform: `translateX(-${currentIndex * 100}%)` }}
        >
          {photos.map((photo, index) => (
            <div key={index} className="relative h-full min-w-full">
              <Image
                src={photo.src}
                alt={photo.alt}
                fill
                className="object-cover"
                priority={index === 0}
              />
              {/* Overlay sutil para mejorar legibilidad si hay texto */}
              <div className="absolute inset-0 bg-black/10"></div>
            </div>
          ))}
        </div>

        {/* Controles de navegación */}
        <button
          onClick={goToPrevious}
          className="absolute top-1/2 left-4 z-10 -translate-y-1/2 rounded-full bg-white/80 p-2 shadow-lg transition-all duration-200 hover:bg-white/95 dark:bg-gray-800/80 dark:hover:bg-gray-800/95"
          aria-label="Imagen anterior"
        >
          <svg
            className="h-5 w-5 text-gray-800 dark:text-gray-200"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>

        <button
          onClick={goToNext}
          className="absolute top-1/2 right-4 z-10 -translate-y-1/2 rounded-full bg-white/80 p-2 shadow-lg transition-all duration-200 hover:bg-white/95 dark:bg-gray-800/80 dark:hover:bg-gray-800/95"
          aria-label="Siguiente imagen"
        >
          <svg
            className="h-5 w-5 text-gray-800 dark:text-gray-200"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
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
            className={`h-3 w-3 rounded-full transition-all duration-200 ${
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
