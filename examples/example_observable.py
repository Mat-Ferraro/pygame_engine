"""
Observable[T] — reactive values, weak references, transactions,
and SubscriptionGroup for automatic scene cleanup.

Demonstrates:
  - Basic subscribe / notify / unsubscribe
  - (old_value, new_value) subscriber signature
  - Weak reference subscriptions (bound method auto-cleanup)
  - Transaction batching
  - SubscriptionGroup for grouped lifecycle management
  - Scene.subscriptions pattern for zero-boilerplate cleanup

Controls:
  SPACE  — change a value and fire listeners
  T      — run a transaction (batch 3 changes, fire once)
  W      — run the weak-ref demo (create and delete an object)
  G      — demonstrate SubscriptionGroup dispose
  ESC    — quit
"""

from __future__ import annotations

import gc

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.state import Observable, SubscriptionGroup
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label, LogPanel, Stack
from pygame_engine.ui.controls.button import Button


# ── Helper — a class whose method we subscribe as a weak ref ─────────────────

class WeakRefTarget:
    """
    Subscribes its bound method to an observable.
    When this object is deleted, the subscription is silently removed.
    """

    def __init__(self, log: LogPanel) -> None:
        self._log = log

    def on_change(self, old: int, new: int) -> None:
        self._log.append(
            f"  WeakRefTarget.on_change: {old} → {new}",
            colour=(180, 220, 180),
        )


# ── Main demo scene ───────────────────────────────────────────────────────────

class ObservableScene(Scene):
    """
    Interactive demonstration of Observable[T] features.

    self.subscriptions is used for the HUD label subscriptions so the
    scene demonstrates its own teardown pattern.
    """

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

        # ── The observables we demonstrate ────────────────────────────────────
        self._counter:    Observable[int]  = Observable(0)
        self._event_count: Observable[int] = Observable(0)

        # Weak-ref demo — we'll create and delete one of these
        self._weak_target: WeakRefTarget | None = None

        # SubscriptionGroup demo
        self._demo_group: SubscriptionGroup = SubscriptionGroup()

    def on_enter(self) -> None:
        theme  = get_theme()
        screen = self._app.screen_rect

        # ── Log panel (the main output) ───────────────────────────────────────
        self._log = LogPanel(
            rect=pygame.Rect(20, 80, screen.width - 40, screen.height - 260),
            max_lines=200,
        )
        self._log.append("Observable[T] demo — use the buttons or keyboard")
        self._log.append("Subscriber signature: callback(old_value, new_value)")
        self._log.append("")

        # ── Status labels — subscribed via self.subscriptions ─────────────────
        self._counter_label = Label(
            pygame.Rect(0, 0, 300, 28),
            f"counter: {self._counter.value}",
            font_size=theme.typography.md,
        )
        self._events_label = Label(
            pygame.Rect(0, 0, 300, 28),
            f"total events fired: {self._event_count.value}",
            font_size=theme.typography.md,
        )

        # Subscribe labels to observables through the scene's group so they
        # are automatically unsubscribed when this scene exits
        self.subscriptions.on(
            self._counter,
            lambda old, new: self._counter_label.set_text(f"counter: {new}"),
        )
        self.subscriptions.on(
            self._event_count,
            lambda old, new: self._events_label.set_text(
                f"total events fired: {new}"
            ),
        )

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_rects = column(
            bounds=pygame.Rect(screen.width - 240, 80, 220, 500),
            count=5,
            item_height=44,
            gap=8,
        )
        btn_change = Button(
            btn_rects[0], "SPACE — change value",
            on_click=self._demo_basic,
        )
        btn_transaction = Button(
            btn_rects[1], "T — transaction",
            on_click=self._demo_transaction,
        )
        btn_weak = Button(
            btn_rects[2], "W — weak ref demo",
            on_click=self._demo_weak_ref,
        )
        btn_group = Button(
            btn_rects[3], "G — group dispose",
            on_click=self._demo_group_dispose,
        )
        btn_quit = Button(
            btn_rects[4], "ESC — quit",
            on_click=lambda: self._app.stop(),
        )

        # ── Layout ────────────────────────────────────────────────────────────
        label_rects = column(
            bounds=pygame.Rect(20, screen.height - 170, 460, 140),
            count=2,
            item_height=28,
            gap=8,
        )
        self._counter_label.set_rect(label_rects[0])
        self._events_label.set_rect(label_rects[1])

        root = Stack(pygame.Rect(screen))
        root.add(self._log)
        root.add(self._counter_label)
        root.add(self._events_label)
        root.add(btn_change)
        root.add(btn_transaction)
        root.add(btn_weak)
        root.add(btn_group)
        root.add(btn_quit)

        title = Label(
            anchor(pygame.Rect(0, 0, 500, 30), screen, "top_center",
                   offset=(0, 16)),
            "Observable[T] — reactive values, weak refs, transactions",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
        )
        root.add(title)

        self.root_widget = root
        self._demo_basic_subscribe()

    def _demo_basic_subscribe(self) -> None:
        """Subscribe a plain function to the counter for the log."""
        def on_counter_change(old: int, new: int) -> None:
            self._log.append(
                f"[basic] counter changed: {old} → {new}",
                colour=(200, 200, 255),
            )
            self._event_count.value = self._event_count.value + 1

        # Store fn reference so it isn't GC'd (plain function = strong ref)
        self._on_counter_change = on_counter_change
        self._counter.subscribe(on_counter_change)

    def _demo_basic(self) -> None:
        self._log.append("")
        self._log.append("── Basic subscribe / notify ──────────")
        self._counter.value = self._counter.value + 1

    def _demo_transaction(self) -> None:
        self._log.append("")
        self._log.append("── Transaction (3 changes → 1 event) ─")
        self._log.append("  Starting transaction...")

        event_before = self._event_count.value

        with self._counter.transaction():
            self._counter.value = self._counter.value + 10
            self._counter.value = self._counter.value + 10
            self._counter.value = self._counter.value + 10

        events_fired = self._event_count.value - event_before
        self._log.append(
            f"  3 assignments → {events_fired} event(s) fired"
            f"  (counter now {self._counter.value})",
            colour=(255, 220, 120),
        )

    def _demo_weak_ref(self) -> None:
        self._log.append("")
        self._log.append("── Weak reference cleanup ─────────────")

        if self._weak_target is None:
            # Create an object and subscribe its bound method
            self._weak_target = WeakRefTarget(self._log)
            self._counter.subscribe(self._weak_target.on_change)
            listeners_before = self._counter.listener_count
            self._log.append(
                f"  Created WeakRefTarget, subscribed bound method",
            )
            self._log.append(
                f"  listener_count = {listeners_before}",
            )
            self._log.append("  Press W again to delete it and trigger GC")
        else:
            # Delete the object — the weak ref should die
            listeners_before = self._counter.listener_count
            del self._weak_target
            self._weak_target = None
            gc.collect()

            listeners_after = self._counter.listener_count
            self._log.append(
                f"  Deleted WeakRefTarget — GC collected",
                colour=(255, 160, 80),
            )
            self._log.append(
                f"  listener_count: {listeners_before} → {listeners_after}",
                colour=(255, 160, 80),
            )
            self._log.append(
                "  Next counter change will NOT call the deleted object's method"
            )
            # Trigger a change to prove no call happens
            self._counter.value = self._counter.value + 1

    def _demo_group_dispose(self) -> None:
        self._log.append("")
        self._log.append("── SubscriptionGroup.dispose() ────────")

        if self._demo_group.subscription_count == 0:
            # Set up the group
            extra_calls: list[str] = []

            def group_listener_a(old: int, new: int) -> None:
                self._log.append(
                    f"  [group-A] counter: {old} → {new}",
                    colour=(180, 255, 180),
                )

            def group_listener_b(old: int, new: int) -> None:
                self._log.append(
                    f"  [group-B] counter: {old} → {new}",
                    colour=(180, 255, 220),
                )

            self._group_listener_a = group_listener_a
            self._group_listener_b = group_listener_b
            self._demo_group.on(self._counter, group_listener_a)
            self._demo_group.on(self._counter, group_listener_b)
            self._log.append(
                f"  Added 2 subscriptions to group "
                f"(total: {self._demo_group.subscription_count})"
            )
            self._log.append(
                "  Triggering a change — both group listeners should fire:"
            )
            self._counter.value = self._counter.value + 1
            self._log.append(
                "  Press G again to dispose() the group"
            )
        else:
            # Dispose the group
            count_before = self._demo_group.subscription_count
            self._demo_group.dispose()
            self._log.append(
                f"  group.dispose() called ({count_before} subs → 0)",
                colour=(255, 160, 80),
            )
            self._log.append("  Triggering a change — group listeners silent:")
            self._counter.value = self._counter.value + 1
            self._log.append(
                "  Group can be reused — press G to add new subscriptions"
            )

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_ESCAPE:
            self._app.stop()
            return True
        if event.key == pygame.K_SPACE:
            self._demo_basic()
            return True
        if event.key == pygame.K_t:
            self._demo_transaction()
            return True
        if event.key == pygame.K_w:
            self._demo_weak_ref()
            return True
        if event.key == pygame.K_g:
            self._demo_group_dispose()
            return True
        return False

    def on_exit(self) -> None:
        # self.subscriptions.dispose() is called automatically by super()
        # This demonstrates the zero-boilerplate cleanup pattern.
        super().on_exit()

    def update(self, dt: float) -> None:
        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)


# ── Entry point ───────────────────────────────────────────────────────────────

def run() -> None:
    """Run the Observable demo."""
    app = Application(AppConfig(
        title="Observable[T] Demo",
        width=900,
        height=620,
    ))
    app.run(lambda: ObservableScene(app))


if __name__ == "__main__":
    run()
