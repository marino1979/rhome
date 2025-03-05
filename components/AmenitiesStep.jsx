import React, { useState, useEffect } from 'react';
import { Check } from 'lucide-react';

const AmenitiesStep = ({ selectedAmenities = [], onChange }) => {
  const [amenityCategories, setAmenityCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAmenities = async () => {
      try {
        const response = await fetch('/appartamenti/api/amenity-categories/');
        const data = await response.json();
        setAmenityCategories(data);
        setLoading(false);
      } catch (error) {
        console.error('Errore nel caricamento dei servizi:', error);
        setLoading(false);
      }
    };
    fetchAmenities();
  }, []);

  const toggleAmenity = (amenityId) => {
    const safeSelected = Array.isArray(selectedAmenities) ? selectedAmenities : [];
    const newSelected = safeSelected.includes(amenityId)
      ? safeSelected.filter(id => id !== amenityId)
      : [...safeSelected, amenityId];
    onChange(newSelected);
  };

  return (
    <div className="space-y-6">
      {loading ? (
        <div className="text-center">Caricamento...</div>
      ) : (
        amenityCategories.map(category => (
          <div key={category.id} className="border rounded-lg p-4">
            <h3 className="text-lg font-medium mb-4">{category.name}</h3>
            <div className="grid grid-cols-2 gap-4">
              {category.amenities.map(amenity => (
                <div
                  key={amenity.id}
                  onClick={() => toggleAmenity(amenity.id)}
                  className={`cursor-pointer p-2 border rounded-lg transition ${Array.isArray(selectedAmenities) && selectedAmenities.includes(amenity.id) ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}
                >
                  {amenity.name}
                  {Array.isArray(selectedAmenities) && selectedAmenities.includes(amenity.id) && <Check className="ml-2 text-blue-500" />}
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default AmenitiesStep;
