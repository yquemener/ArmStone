import pygame

pygame.init()

def main():
    # This dict can be left as-is, since pygame will generate a
    # pygame.JOYDEVICEADDED event for every joystick connected
    # at the start of the program.
    joysticks = {0:pygame.joystick.Joystick(0)}
    clock = pygame.time.Clock()

    done = False
    while not done:
        pygame.event.get()
        #     if event.type == pygame.QUIT:
        #         done = True  # Flag that we are done so we exit this loop.
                
        joystick_count = pygame.joystick.get_count()

        print(f"Number of joysticks: {joystick_count}")

        # For each joystick:
        for joystick in joysticks.values():
            print("hop")
            jid = joystick.get_instance_id()

            # Get the name from the OS for the controller/joystick.
            name = joystick.get_name()
            print(f"Joystick name: {name}")

            guid = joystick.get_guid()
            print(f"GUID: {guid}")

            power_level = joystick.get_power_level()
            print(f"Joystick's power level: {power_level}")

            # Usually axis run in pairs, up/down for one, and left/right for
            # the other. Triggers count as axes.
            axes = joystick.get_numaxes()
            print(f"Number of axes: {axes}")

            for i in range(axes):
                axis = joystick.get_axis(i)
                print(f"Axis {i} value: {axis:>6.3f}")

            buttons = joystick.get_numbuttons()
            print(f"Number of buttons: {buttons}")

            for i in range(buttons):
                button = joystick.get_button(i)
                print(f"Button {i:>2} value: {button}")

        # Limit to 30 frames per second.
        clock.tick(30)

if __name__ == "__main__":
    main()
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()