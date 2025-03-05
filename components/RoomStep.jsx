import React, { useState, useEffect } from 'react';
import { Plus, Minus, Trash } from 'lucide-react';

const RoomStep = ({ rooms = [], onChange }) => {  // Aggiungiamo un default empty array
  const [roomTypes, setRoomTypes] = useState([]);
  const [bedTypes, setBedTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Simuliamo i dati per ora - in produzione useresti le API reali
        setRoomTypes([
          { id: 1, name: 'Camera da Letto' },
          { id: 2, name: 'Soggiorno' },
          { id: 3, name: 'Cucina' }
        ]);
        setBedTypes([
          { id: 1, name: 'Letto Matrimoniale' },
          { id: 2, name: 'Letto Singolo' },
          { id: 3, name: 'Divano Letto' }
        ]);
        setLoading(false);
      } catch (error) {
        setError('Errore nel caricamento dei dati');
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const addRoom = () => {
    const currentRooms = Array.isArray(rooms) ? rooms : [];
    onChange([...(Array.isArray(rooms) ? rooms : []), {
      name: '',
      room_type: '',
      square_meters: '',
      beds: []
    }]);
  };

  const removeRoom = (index) => {
    const newRooms = [...rooms];
    newRooms.splice(index, 1);
    onChange(newRooms);
  };

  const updateRoom = (index, field, value) => {
    const newRooms = Array.isArray(rooms) ? [...rooms] : [];
    newRooms[index] = { ...newRooms[index], [field]: value };
    onChange(newRooms);
  };

  const addBed = (roomIndex) => {
    const newRooms = [...rooms];
    if (!newRooms[roomIndex].beds) {
      newRooms[roomIndex].beds = [];
    }
    newRooms[roomIndex].beds.push({ bed_type: '', quantity: 1 });
    onChange(newRooms);
  };

  const removeBed = (roomIndex, bedIndex) => {
    const newRooms = [...rooms];
    newRooms[roomIndex].beds.splice(bedIndex, 1);
    onChange(newRooms);
  };

  const updateBed = (roomIndex, bedIndex, field, value) => {
    const newRooms = [...rooms];
    if (!newRooms[roomIndex].beds[bedIndex]) {
      newRooms[roomIndex].beds[bedIndex] = {};
    }
    newRooms[roomIndex].beds[bedIndex] = {
      ...newRooms[roomIndex].beds[bedIndex],
      [field]: value
    };
    onChange(newRooms);
  };

  if (loading) {
    return <div className="text-center py-4">Caricamento...</div>;
  }

  if (error) {
    return <div className="text-center text-red-500 py-4">{error}</div>;
  }

  return (
    <div className="space-y-6">
      {/* Se rooms è undefined o vuoto, mostriamo un messaggio */}
      {(!rooms || rooms.length === 0) && (
        <div className="text-center text-gray-500 py-4">
          Non ci sono ancora stanze. Aggiungi la tua prima stanza!
        </div>
      )}

      {/* Iteriamo solo se rooms è un array valido */}
      {Array.isArray(rooms) && rooms.map((room, roomIndex) => (
        <div key={roomIndex} className="border rounded-lg p-4 bg-gray-50">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-medium">Stanza {roomIndex + 1}</h3>
            <button
              onClick={() => removeRoom(roomIndex)}
              className="text-red-500 hover:text-red-600 p-1 rounded"
              aria-label="Rimuovi stanza"
            >
              <Trash className="h-5 w-5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome Stanza
              </label>
              <input
                type="text"
                value={room.name || ''}
                onChange={(e) => updateRoom(roomIndex, 'name', e.target.value)}
                className="w-full p-2 border rounded"
                placeholder="es. Camera Principale"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo Stanza
              </label>
              <select
                value={room.room_type || ''}
                onChange={(e) => updateRoom(roomIndex, 'room_type', e.target.value)}
                className="w-full p-2 border rounded"
              >
                <option value="">Seleziona tipo...</option>
                {roomTypes.map(type => (
                  <option key={type.id} value={type.id}>{type.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Metri Quadri
              </label>
              <input
                type="number"
                value={room.square_meters || ''}
                onChange={(e) => updateRoom(roomIndex, 'square_meters', e.target.value)}
                className="w-full p-2 border rounded"
                placeholder="m²"
                min="0"
                step="0.5"
              />
            </div>
          </div>

          <div className="mt-4">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium">Letti nella stanza</h4>
              <button
                onClick={() => addBed(roomIndex)}
                className="flex items-center text-blue-500 hover:text-blue-600"
              >
                <Plus className="h-4 w-4 mr-1" />
                Aggiungi Letto
              </button>
            </div>

            <div className="space-y-2">
              {Array.isArray(room.beds) && room.beds.map((bed, bedIndex) => (
                <div key={bedIndex} className="flex items-center gap-4">
                  <select
                    value={bed.bed_type || ''}
                    onChange={(e) => updateBed(roomIndex, bedIndex, 'bed_type', e.target.value)}
                    className="flex-1 p-2 border rounded"
                  >
                    <option value="">Tipo letto...</option>
                    {bedTypes.map(type => (
                      <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                  </select>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => updateBed(roomIndex, bedIndex, 'quantity', Math.max(1, (bed.quantity || 1) - 1))}
                      className="p-1 border rounded hover:bg-gray-100"
                    >
                      <Minus className="h-4 w-4" />
                    </button>
                    <span className="w-8 text-center">{bed.quantity || 1}</span>
                    <button
                      onClick={() => updateBed(roomIndex, bedIndex, 'quantity', (bed.quantity || 1) + 1)}
                      className="p-1 border rounded hover:bg-gray-100"
                    >
                      <Plus className="h-4 w-4" />
                    </button>
                  </div>

                  <button
                    onClick={() => removeBed(roomIndex, bedIndex)}
                    className="text-red-500 hover:text-red-600 p-1 rounded"
                    aria-label="Rimuovi letto"
                  >
                    <Trash className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}

      <button
        onClick={addRoom}
        className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:text-gray-600 hover:border-gray-400 flex items-center justify-center gap-2"
      >
        <Plus className="h-5 w-5" />
        Aggiungi Stanza
      </button>
    </div>
  );
};

export default RoomStep;