/*
    Библиотека для программного управления Servo (на базе millis/micros)
    Документация: 
    GitHub: https://github.com/GyverLibs/SoftServo
    Возможности:
    - Не использует дополнительный аппаратный таймер
    - Работает на millis() и micros()
    - Синтаксис как у Servo.h
    - Режим работы асинхронный и с delay
    - Повышенная произвводительность для AVR
        
    AlexGyver, alex@alexgyver.ru
    https://alexgyver.ru/
    MIT License

    Версии:
    v1.0 - релиз
    v1.1 - переделан FastIO
    v1.1.1 - убран FastIO
    v1.2 - мелкие фиксы
*/

#ifndef SOFT_SERVO_H
#define SOFT_SERVO_H

#include <Arduino.h>

class SoftServo {
public:
  SoftServo() : _attached(false), _pin(-1), _angle(90), _min(544), _max(2400), 
                _asyncMode(false), _lastUpdate(0) {}
  
  // Подключение сервопривода к пину
  void attach(int pin) {
    attach(pin, 544, 2400);
  }
  
  // Подключение с указанием минимального и максимального значений импульса
  void attach(int pin, int min, int max) {
    _pin = pin;
    _min = min;
    _max = max;
    _attached = true;
    pinMode(_pin, OUTPUT);
    write(90); // Устанавливаем в среднее положение при подключении
  }
  
  // Отключение сервопривода
  void detach() {
    _attached = false;
  }
  
  // Переключение в асинхронный режим
  void asyncMode() {
    _asyncMode = true;
  }
  
  // Переключение в режим задержки
  void delayMode() {
    _asyncMode = false;
  }
  
  // Тикер, нужно вызывать как можно чаще
  bool tick() {
    if (!_attached) return false;
    
    // Обновляем позицию каждые 20 мс
    unsigned long currentMillis = millis();
    if (currentMillis - _lastUpdate >= 20) {
      _lastUpdate = currentMillis;
      
      // Генерация импульса для серво
      digitalWrite(_pin, HIGH);
      
      // Длительность импульса от 544 до 2400 мкс
      unsigned long pulseWidth = map(_angle, 0, 180, _min, _max);
      
      if (_asyncMode) {
        // В асинхронном режиме не блокируем выполнение
        delayMicroseconds(10); // Минимальная задержка для установки пина
        digitalWrite(_pin, LOW);
        return true;
      } else {
        // В режиме с задержкой ждем нужное время
        delayMicroseconds(pulseWidth);
        digitalWrite(_pin, LOW);
      }
    }
    
    return false;
  }
  
  // Установка угла сервопривода (0-180)
  void write(int value) {
    if (value < 0) value = 0;
    if (value > 180) value = 180;
    _angle = value;
  }
  
  // Установка длительности импульса в микросекундах
  void writeMicroseconds(int us) {
    _angle = map(us, _min, _max, 0, 180);
  }
  
  // Получение текущего угла
  int read() {
    return _angle;
  }
  
  // Получение текущей длительности импульса
  int readMicroseconds() {
    return map(_angle, 0, 180, _min, _max);
  }
  
  // Проверка, подключен ли сервопривод
  bool attached() {
    return _attached;
  }
  
private:
  bool _attached;       // Флаг подключения
  int _pin;             // Пин для управления
  int _angle;           // Текущий угол (0-180)
  int _min;             // Минимальная длительность импульса (мкс)
  int _max;             // Максимальная длительность импульса (мкс)
  bool _asyncMode;      // Режим работы (асинхронный/с задержкой)
  unsigned long _lastUpdate; // Время последнего обновления
};

#endif // SOFT_SERVO_H