"""异常体系测试。"""

from __future__ import annotations

from src.core.exceptions import (
    AppException,
    ContentSafetyException,
    ForbiddenException,
    LLMServiceException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
    ValidationException,
)


class TestAppException:
    """基类异常测试。"""

    def test_default_status_code(self) -> None:
        exc = AppException("test")
        assert exc.status_code == 500
        assert exc.message == "test"

    def test_custom_status_code(self) -> None:
        exc = AppException("not found", status_code=404)
        assert exc.status_code == 404

    def test_detail_dict(self) -> None:
        exc = AppException("error", detail={"key": "value"})
        assert exc.detail == {"key": "value"}


class TestNotFoundException:
    def test_not_found(self) -> None:
        exc = NotFoundException("User", "123")
        assert exc.status_code == 404
        assert "User" in exc.message
        assert "123" in exc.message


class TestValidationException:
    def test_validation(self) -> None:
        exc = ValidationException("invalid input", errors=[{"field": "email"}])
        assert exc.status_code == 422


class TestUnauthorizedException:
    def test_unauthorized(self) -> None:
        exc = UnauthorizedException()
        assert exc.status_code == 401


class TestForbiddenException:
    def test_forbidden(self) -> None:
        exc = ForbiddenException("admin only")
        assert exc.status_code == 403


class TestRateLimitException:
    def test_rate_limit(self) -> None:
        exc = RateLimitException(retry_after=30)
        assert exc.status_code == 429
        assert exc.detail["retry_after_seconds"] == 30


class TestLLMServiceException:
    def test_llm_error(self) -> None:
        exc = LLMServiceException("deepseek", "timeout")
        assert exc.status_code == 502
        assert "deepseek" in exc.message


class TestContentSafetyException:
    def test_content_safety(self) -> None:
        exc = ContentSafetyException("violence detected")
        assert exc.status_code == 451


class TestInheritance:
    def test_all_exceptions_inherit_from_app(self) -> None:
        excs = [
            NotFoundException("R", "1"),
            ValidationException("V"),
            UnauthorizedException(),
            ForbiddenException(),
            RateLimitException(),
            LLMServiceException("P", "E"),
            ContentSafetyException("S"),
        ]
        for exc in excs:
            assert isinstance(exc, AppException)

    def test_all_are_catchable(self) -> None:
        """所有异常可被 AppException 捕获。"""
        for exc_cls, kwargs in [
            (NotFoundException, {"resource": "X", "resource_id": "1"}),
            (ValidationException, {"message": "test"}),
            (UnauthorizedException, {}),
            (ForbiddenException, {}),
            (RateLimitException, {}),
            (LLMServiceException, {"provider": "test", "reason": "error"}),
            (ContentSafetyException, {"reason": "test"}),
        ]:
            try:
                raise exc_cls(**kwargs)  # type: ignore[arg-type]
            except AppException:
                pass  # expected
