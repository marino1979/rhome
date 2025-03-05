import React, { useState, useEffect } from 'react';
import { X, Image, ChevronLeft, ChevronRight, Home, MapPin, Bed, Coffee, Camera, DollarSign } from 'lucide-react';
import RoomStep from './RoomStep';
import AmenitiesStep from './AmenitiesStep';
const getCsrfToken = () => {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
};
const ListingWizard = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    basic_info: { title: '', description: '' },
    location: { address: '', total_square_meters: '', outdoor_square_meters: '' },
    rooms: [],
    amenities: [],
    photos: [],
    pricing: { base_price: '', cleaning_fee: '' }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Carica i dati salvati dal backend al mount
  useEffect(() => {
    const fetchSavedData = async () => {
      try {
        const response = await fetch('/appartamenti/api/listing/wizard/');
        const data = await response.json();
        if (data.data) {
          setFormData(data.data);
          setCurrentStep(data.current_step);
        }
      } catch (err) {
        setError('Errore nel caricamento dei dati salvati');
      }
    };
    fetchSavedData();
  }, []);

  const handleSubmitStep = async (direction) => {
    setLoading(true);
    setError(null);
    
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('step', currentStep);
      formDataToSend.append('action', direction);

      // Aggiungi i dati specifici dello step
      const currentStepData = formData[getStepKey(currentStep)];
      if (currentStep === 5) { // Step delle foto
        currentStepData.forEach((file, index) => {
          formDataToSend.append('photos[]', file);
        });
      } else if (currentStep === 4) { // Step dei servizi
        currentStepData.forEach(id => {
          formDataToSend.append('amenities[]', id);
        });
      } else if (currentStep === 3) { // Step delle stanze
        formDataToSend.append('rooms', JSON.stringify(currentStepData));
      } else {
        Object.entries(currentStepData).forEach(([key, value]) => {
          formDataToSend.append(key, value);
        });
      }

      const response = await fetch('/appartamenti/api/listing/wizard/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken()
        },
        body: formDataToSend
      });

      if (!response.ok) {
        throw new Error('Errore nella validazione dei dati');
      }

      const result = await response.json();
      if (result.success) {
        if (direction === 'next') {
          setCurrentStep(prev => Math.min(prev + 1, 6));
        } else {
          setCurrentStep(prev => Math.max(prev - 1, 1));
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFinalSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('action', 'save');
      
      const response = await fetch('/appartamenti/api/listing/wizard/', {
        method: 'POST',
         headers: {
    'X-CSRFToken': getCsrfToken()
  },
        body: formDataToSend
      });

      const result = await response.json();
      if (result.success) {
        // Redirect alla pagina dell'annuncio
        window.location.href = `/listings/${result.listing_id}`;
      } else {
        throw new Error('Errore nel salvataggio dell\'annuncio');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStepKey = (step) => {
    const stepMap = {
      1: 'basic_info',
      2: 'location',
      3: 'rooms',
      4: 'amenities',
      5: 'photos',
      6: 'pricing'
    };
    return stepMap[step];
  };

  const getStepIcon = (step) => {
    const icons = {
      1: <Home />,
      2: <MapPin />,
      3: <Bed />,
      4: <Coffee />,
      5: <Camera />,
      6: <DollarSign />
    };
    return icons[step];
  };

  const renderStepContent = () => {
    const stepKey = getStepKey(currentStep);
    const stepData = formData[stepKey] || {};
 
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Titolo Annuncio
              </label>
              <input
                type="text"
                value={stepData.title || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  basic_info: { title: e.target.value, description: stepData.description || '' }
                })}
                className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
                placeholder="Inserisci il titolo del tuo annuncio"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Descrizione
              </label>
              <textarea
                value={stepData.description || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  basic_info: { title: stepData.title || '', description: e.target.value }
                })}
                className="w-full p-2 border rounded h-32 focus:ring-2 focus:ring-blue-500"
                placeholder="Descrivi il tuo appartamento"
              />
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Indirizzo
              </label>
              <input
                type="text"
                value={stepData.address || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  location: { ...stepData, address: e.target.value }
                })}
                className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
                placeholder="Indirizzo completo"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Metri Quadri Totali
                </label>
                <input
                  type="number"
                  value={stepData.total_square_meters || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    location: { ...stepData, total_square_meters: e.target.value }
                  })}
                  className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
                  placeholder="m²"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Metri Quadri Esterni
                </label>
                <input
                  type="number"
                  value={stepData.outdoor_square_meters || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    location: { ...stepData, outdoor_square_meters: e.target.value }
                  })}
                  className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
                  placeholder="m² esterni"
                />
              </div>
            </div>
          </div>
        );
        case 3:
            return (
              <RoomStep
                rooms={stepData}
                onChange={(rooms) => setFormData({
                  ...formData,
                  rooms: rooms
                })}
              />
            );
          
          case 4:
            return (
              <AmenitiesStep
                selectedAmenities={stepData}
                onChange={(amenities) => setFormData({
                  ...formData,
                  amenities: amenities
                })}
              />
            );
            case 5:
              return (
                <div>
                  <div 
                    className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-6"
                    onDrop={(e) => {
                      e.preventDefault();
                      const files = Array.from(e.dataTransfer.files);
                      const currentPhotos = Array.isArray(stepData) ? stepData : [];
                      setFormData({
                        ...formData,
                        photos: [...currentPhotos, ...files]
                      });
                    }}
                    onDragOver={(e) => e.preventDefault()}
                  >
                    <Image className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <div className="text-gray-600">
                      Trascina le foto qui o 
                      <label className="ml-1 text-blue-500 hover:text-blue-600 cursor-pointer">
                        <input 
                          type="file" 
                          multiple 
                          accept="image/*" 
                          className="hidden"
                          onChange={(e) => {
                            const files = Array.from(e.target.files);
                            const currentPhotos = Array.isArray(stepData) ? stepData : [];
                            setFormData({
                              ...formData,
                              photos: [...currentPhotos, ...files]
                            });
                          }}
                        />
                        selezionale dal computer
                      </label>
                    </div>
                  </div>
            
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {Array.isArray(stepData) && stepData.map((file, index) => (
                      <div key={index} className="relative">
                        <img 
                          src={URL.createObjectURL(file)}
                          alt={`Preview ${index + 1}`}
                          className="w-full h-48 object-cover rounded"
                        />
                        <button
                          onClick={() => {
                            const newPhotos = [...stepData];
                            newPhotos.splice(index, 1);
                            setFormData({
                              ...formData,
                              photos: newPhotos
                            });
                          }}
                          className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              );
      case 6:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Prezzo Base (per notte)
              </label>
              <input
                type="number"
                value={stepData.base_price || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  pricing: { ...stepData, base_price: e.target.value }
                })}
                className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
                placeholder="€"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Costo Pulizie
              </label>
              <input
                type="number"
                value={stepData.cleaning_fee || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  pricing: { ...stepData, cleaning_fee: e.target.value }
                })}
                className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
                placeholder="€"
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between">
          {[1, 2, 3, 4, 5, 6].map((step) => (
            <div 
              key={step} 
              className={`w-12 h-12 rounded-full flex items-center justify-center border-2
                ${currentStep >= step 
                  ? 'border-blue-500 text-blue-500' 
                  : 'border-gray-300 text-gray-300'}`}
            >
              {getStepIcon(step)}
            </div>
          ))}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Step Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {renderStepContent()}

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8">
          <button
            onClick={() => handleSubmitStep('prev')}
            disabled={currentStep === 1 || loading}
            className="flex items-center px-4 py-2 border rounded text-gray-600 hover:bg-gray-50 disabled:opacity-50"
          >
            <ChevronLeft className="h-4 w-4 mr-2" />
            Indietro
          </button>
          
          {currentStep === 6 ? (
            <button
              onClick={handleFinalSubmit}
              disabled={loading}
              className="flex items-center px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
            >
              {loading ? 'Salvataggio...' : 'Pubblica Annuncio'}
            </button>
          ) : (
            <button
              onClick={() => handleSubmitStep('next')}
              disabled={loading}
              className="flex items-center px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              Avanti
              <ChevronRight className="h-4 w-4 ml-2" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ListingWizard;