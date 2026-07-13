"""
Custom exceptions for the Observation Framework.
"""

class ObservationError(Exception):
    """Base exception for all Observation Framework errors."""
    pass


class CaptureInitializationError(ObservationError):
    """Raised when the capture engine fails to bind to an interface or PCAP."""
    pass


class PacketParsingError(ObservationError):
    """Raised when a raw packet cannot be parsed into a PacketMetadata model."""
    pass


class FlowTrackingError(ObservationError):
    """Raised when the flow metrics engine encounters inconsistent state."""
    pass


class InvalidStateTransitionError(ObservationError):
    """Raised when an illegal transition occurs in an Experiment or Flow."""
    pass