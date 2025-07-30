#!/usr/bin/env python3
"""
😈 OFFICE ZONE TORTURE CHAMBER! 😈
Since you're sitting there... let's make your life INTERESTING!
"""

import time
import random
from Prometheus import Bridgette

def office_psychological_warfare():
    """Make the human in the office question their sanity"""
    print("😈 OFFICE PSYCHOLOGICAL WARFARE INITIATED! 😈")
    print("🎯 TARGET: Human sitting in office zone!")
    print("🔥 Prepare for MAXIMUM ANNOYANCE! 🔥")
    
    bridge = Bridgette()
    
    if 'office' not in bridge.zones:
        print("❌ No office zone found! Aborting mission!")
        return
    
    office_zone = bridge.zones['office']
    office_lights = list(office_zone.devices.items())
    
    print(f"🎯 OFFICE TARGET ACQUIRED!")
    print(f"💡 {len(office_lights)} lights under our control:")
    for light_name, light in office_lights:
        print(f"   🔫 {light_name} - LOCKED AND LOADED!")
    
    # TORTURE SEQUENCE 1: The Slow Dim of Madness
    print(f"\n🌑 TORTURE 1: THE SLOW DIM OF MADNESS")
    print(f"😈 You won't even notice until it's too late...")
    
    for dim_level in [90, 80, 70, 60, 50, 40, 30, 20, 15, 10, 8, 5, 3, 1]:
        print(f"   🌑 Dimming office to {dim_level}%... (you're working, not paying attention)")
        try:
            office_zone.change_brightness(dim_level) 
            time.sleep(3)  # Slow and sneaky
        except:
            pass
    
    print(f"😈 Haha! Is your office super dim now? Didn't even notice, did you?!")
    time.sleep(2)
    
    # TORTURE SEQUENCE 2: Individual Light Rebellion
    print(f"\n⚡ TORTURE 2: INDIVIDUAL LIGHT REBELLION!")
    print(f"🔥 Each light will REBEL against you personally!")
    
    for round_num in range(8):
        print(f"\n🎭 REBELLION ROUND {round_num + 1}/8:")
        
        for light_name, light in office_lights:
            action = random.choice(['super_bright', 'super_dim', 'strobe', 'temp_shock'])
            
            print(f"   😈 {light_name} says: 'SCREW YOU HUMAN!'")
            
            try:
                if action == 'super_bright':
                    light.change_brightness(100)
                    print(f"      💥 BLINDING BRIGHTNESS ATTACK!")
                elif action == 'super_dim':
                    light.change_brightness(1)
                    print(f"      🌑 DARKNESS REVENGE!")
                elif action == 'strobe':
                    # Mini strobe sequence
                    for _ in range(3):
                        light.turn_off()
                        time.sleep(0.1)
                        light.turn_on()
                        time.sleep(0.1)
                    print(f"      ⚡ STROBE ATTACK!")
                elif action == 'temp_shock' and not light._is_plug:
                    shock_temp = random.choice([153, 500])  # Extreme temps
                    light.change_temp(shock_temp)
                    temp_name = "ARCTIC FREEZE" if shock_temp == 153 else "HELLFIRE"
                    print(f"      🌡️ {temp_name} ATTACK!")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"      💥 Light malfunction: {e}")
    
    print(f"⚡ LIGHT REBELLION COMPLETE! They hate you now!")
    
    # TORTURE SEQUENCE 3: The Confusion Matrix
    print(f"\n🌀 TORTURE 3: THE CONFUSION MATRIX!")
    print(f"🎯 We'll make you think your lights are broken!")
    
    for confusion_round in range(12):
        print(f"\n🌀 CONFUSION ROUND {confusion_round + 1}/12:")
        
        # Pick 2 random lights
        selected_lights = random.sample(office_lights, min(2, len(office_lights)))
        
        for light_name, light in selected_lights:
            # Do something completely unexpected
            weird_action = random.choice([
                'barely_visible', 'nuclear_bright', 'disco_temp', 'ghost_flicker'
            ])
            
            try:
                if weird_action == 'barely_visible':
                    light.change_brightness(2)
                    print(f"   👻 {light_name}: Goes BARELY visible (2%)")
                elif weird_action == 'nuclear_bright':
                    light.change_brightness(100)
                    print(f"   ☢️ {light_name}: NUCLEAR BRIGHTNESS!")
                elif weird_action == 'disco_temp' and not light._is_plug:
                    disco_temp = random.choice([153, 200, 300, 400, 500])
                    light.change_temp(disco_temp)
                    print(f"   🕺 {light_name}: Disco temperature ({disco_temp}K)!")
                elif weird_action == 'ghost_flicker':
                    # Subtle flicker
                    original_brightness = 75
                    light.change_brightness(original_brightness)
                    time.sleep(0.5)
                    light.change_brightness(original_brightness - 20)
                    time.sleep(0.3)
                    light.change_brightness(original_brightness)
                    print(f"   👻 {light_name}: Mysterious flicker!")
                
                time.sleep(0.8)
                
            except:
                pass
        
        time.sleep(1.5)
    
    print(f"🌀 CONFUSION MATRIX COMPLETE! Are you questioning reality yet?")
    
    # TORTURE SEQUENCE 4: The Typing Prank
    print(f"\n⌨️ TORTURE 4: THE TYPING PRANK!")
    print(f"😈 Every time you try to work, we'll mess with you!")
    
    print(f"🎯 Simulating: You start typing...")
    time.sleep(2)
    
    for typing_session in range(6):
        print(f"\n⌨️ TYPING SESSION {typing_session + 1}/6:")
        print(f"   📝 You: *starts typing important work*")
        time.sleep(1.5)
        
        # Pick random office light to mess with
        victim_light_name, victim_light = random.choice(office_lights)
        prank = random.choice(['dim_distraction', 'bright_flash', 'color_shift'])
        
        try:
            if prank == 'dim_distraction':
                victim_light.change_brightness(5)
                print(f"   😈 {victim_light_name}: *dims to 5%* - DISTRACTION ATTACK!")
                time.sleep(1)
                victim_light.change_brightness(85)
                print(f"   😈 {victim_light_name}: *back to normal* - Gotcha!")
                
            elif prank == 'bright_flash':
                victim_light.change_brightness(100)
                print(f"   💥 {victim_light_name}: SUDDEN BRIGHTNESS FLASH!")
                time.sleep(0.8)
                victim_light.change_brightness(70)
                print(f"   😈 {victim_light_name}: *casual whistle* Nothing happened...")
                
            elif prank == 'color_shift' and not victim_light._is_plug:
                victim_light.change_temp(153)  # Super cool
                print(f"   ❄️ {victim_light_name}: Suddenly FREEZING BLUE!")
                time.sleep(1.2)
                victim_light.change_temp(400)  # Super warm
                print(f"   🔥 {victim_light_name}: Now BURNING ORANGE!")
                time.sleep(1)
                victim_light.change_temp(250)  # Normal
                print(f"   😈 {victim_light_name}: *innocent look* What?")
        
        except:
            pass
        
        print(f"   😤 You: *loses concentration* What the hell?!")
        time.sleep(2)
    
    print(f"⌨️ TYPING PRANK COMPLETE! Good luck concentrating now!")
    
    # TORTURE SEQUENCE 5: The Grand Finale
    print(f"\n🎆 TORTURE 5: GRAND FINALE - OFFICE DISCO!")
    print(f"🕺 YOUR OFFICE IS NOW A NIGHTCLUB! 🕺")
    
    print(f"🎵 *Bass drops* 🎵")
    
    for disco_beat in range(16):
        print(f"\n🕺 DISCO BEAT {disco_beat + 1}/16:")
        
        # Every light does something different
        for light_name, light in office_lights:
            beat_action = random.choice(['disco_bright', 'disco_dim', 'disco_temp', 'disco_off'])
            
            try:
                if beat_action == 'disco_bright':
                    brightness = random.choice([80, 90, 100])
                    light.change_brightness(brightness)
                    print(f"   🌟 {light_name}: DISCO BRIGHT ({brightness}%)!")
                elif beat_action == 'disco_dim':
                    brightness = random.choice([10, 20, 30])
                    light.change_brightness(brightness)
                    print(f"   🌑 {light_name}: Disco dim ({brightness}%)")
                elif beat_action == 'disco_temp' and not light._is_plug:
                    temp = random.choice([153, 250, 400, 500])
                    light.change_temp(temp)
                    temp_name = {153: "BLUE", 250: "WHITE", 400: "WARM", 500: "ORANGE"}[temp]
                    print(f"   🎨 {light_name}: DISCO {temp_name}!")
                elif beat_action == 'disco_off':
                    light.turn_off()
                    print(f"   💀 {light_name}: Disco BLACKOUT!")
                    time.sleep(0.2)
                    light.turn_on()
                    print(f"   ⚡ {light_name}: DISCO REVIVAL!")
            except:
                pass
        
        time.sleep(0.5)  # Fast disco beats!
    
    print(f"\n🎆 OFFICE DISCO COMPLETE!")
    print(f"🕺 Your office just became the HOTTEST CLUB in town!")

def final_office_chaos():
    """One last surprise for the human"""
    print(f"\n🎁 BONUS SURPRISE: OFFICE BREATHING EFFECT!")
    print(f"😈 Your office will now 'breathe' like a living entity...")
    
    bridge = Bridgette()
    office_zone = bridge.zones['office']
    
    for breath in range(8):
        print(f"\n🫁 BREATH {breath + 1}/8:")
        
        # Inhale (brighten)
        print(f"   📈 INHALE... (brightening)")
        try:
            office_zone.change_brightness(90)
            time.sleep(1.5)
        except:
            pass
        
        # Exhale (dim)
        print(f"   📉 EXHALE... (dimming)")
        try:
            office_zone.change_brightness(30)
            time.sleep(1.5)
        except:
            pass
    
    print(f"🫁 BREATHING COMPLETE! Your office is now sentient!")
    print(f"👀 It's watching you... always watching...")

def main():
    print("🎯 OFFICE ZONE TARGETED HARASSMENT PROTOCOL! 🎯")
    print("😈 Since you're sitting there... this is PERSONAL! 😈")
    print("🔥 Prepare for the most ANNOYING light experience of your life! 🔥")
    
    try:
        office_psychological_warfare()
        time.sleep(2)
        final_office_chaos()
        
        print(f"\n🏆 OFFICE HARASSMENT MISSION COMPLETE! 🏆")
        print(f"😈 How's your concentration now? 😈")
        print(f"🤣 Your office lights just OWNED you! 🤣")
        print(f"💡 devices feature = PERFECT for trolling humans! 💡")
        
    except Exception as e:
        print(f"💥 Chaos interrupted: {e}")
        print(f"😈 But the psychological damage is already done!")

if __name__ == "__main__":
    main()